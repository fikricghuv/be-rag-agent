# app/services/chat_history_service.py
from uuid import UUID
import logging 
from sqlalchemy.orm import Session
from sqlalchemy import func, select, literal_column, column, extract, Float
from sqlalchemy.sql import select, func, distinct, desc, exists
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError 
from fastapi import Depends 
from typing import List, Dict, Any, Optional
from collections import defaultdict
from database.models import Chat, RoomConversation, Member
from core.config_db import config_db
from sqlalchemy import TEXT, Text
from dateutil.relativedelta import relativedelta, SU
from schemas.chat_history_schema import PaginatedChatHistoryResponse, ChatHistoryResponse
from sqlalchemy import or_, func, desc
from sqlalchemy import cast, String
from exceptions.custom_exceptions import ServiceException, DatabaseException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatHistoryService:
    """
    Service class untuk mengelola operasi terkait riwayat chat dan statistik.
    """
    def __init__(self, db: Session):
        """
        Inisialisasi ChatHistoryService dengan sesi database.

        Args:
            db: SQLAlchemy Session object.
        """
        self.db = db

    def _get_conversation_counts_by_period(self, group_format: str, start_date: datetime, end_date: datetime, client_id: UUID) -> Dict[
        str, int]:
        """
        Helper private untuk mendapatkan jumlah percakapan berdasarkan format grup periode.
        Digunakan oleh metode weekly, monthly, yearly.
        """
        try:
            if self.db.bind.name == 'postgresql':
                period_expr = func.to_char(Chat.created_at, group_format)
            elif self.db.bind.name == 'mysql':
                period_expr = func.date_format(Chat.created_at, group_format)
            else:  # SQLite
                period_expr = func.strftime(group_format, Chat.created_at)

            query_results = self.db.query(
                period_expr.label("period"),
                func.count(distinct(Chat.id)).label("total_conversations")
            ).filter(
                Chat.created_at >= start_date,
                Chat.created_at <= end_date,
                Chat.client_id == client_id
            ).group_by("period").all()

            return {row.period: row.total_conversations for row in query_results}
        
        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][CHAT_HISTORY] SQL error at get_categories_by_frequency: {e}", exc_info=True)
            raise DatabaseException("CHAT_HISTORY_DB_ERROR", "Failed to fetch category frequency from database.")


    def get_conversations_by_week(self, client_id: UUID) -> Dict[str, int]:
        """
        Mendapatkan jumlah percakapan per minggu (ISO Week),
        dengan kunci berupa tanggal Minggu terakhir dari minggu tersebut (YYYY-MM-DD).
        """
        final_weekly_stats: Dict[str, int] = {}
        today = datetime.now()

        start_date_for_query = today + relativedelta(weeks=-12, weekday=SU(-1))
        end_date_for_query = today.replace(hour=23, minute=59, second=59, microsecond=999999)

        db_group_format = 'IYYY-IW'

        raw_data_iso_week = self._get_conversation_counts_by_period(db_group_format, start_date_for_query,
                                                                    end_date_for_query, client_id)
        first_sunday_in_range = today + relativedelta(weeks=-11, weekday=SU)

        for i in range(12): 
            
            current_sunday = first_sunday_in_range + timedelta(weeks=i)

            iso_year, iso_week, _ = current_sunday.isocalendar()
            week_key_iso = f"{iso_year}-{iso_week:02d}"

            final_date_key = current_sunday.strftime('%Y-%m-%d')

            final_weekly_stats[final_date_key] = raw_data_iso_week.get(week_key_iso, 0)

        sorted_keys = sorted(final_weekly_stats.keys())
        return {k: final_weekly_stats[k] for k in sorted_keys}

    def get_conversations_by_month(self, client_id: UUID) -> Dict[str, int]:
        today = datetime.now()
        start_date = (today.replace(day=1) - timedelta(days=365)).replace(day=1)
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)

        db_group_format = {
            'postgresql': 'YYYY-MM',
            'mysql': '%Y-%m',
            'sqlite': '%Y-%m'
        }.get(self.db.bind.name, '%Y-%m')

        raw_data = self._get_conversation_counts_by_period(db_group_format, start_date, end_date, client_id)

        result = {}
        for i in range(12):
            month_date = (today.replace(day=1) - timedelta(days=30 * (11 - i)))
            accurate_month = (today.month - 11 + i - 1) % 12 + 1
            accurate_year = today.year + ((today.month - 11 + i - 1) // 12)
            month_date = datetime(accurate_year, accurate_month, 1)
            month_key = month_date.strftime('%Y-%m')
            result[month_key] = raw_data.get(month_key, 0)

        return result

    def get_conversations_by_year(self, client_id: UUID) -> Dict[str, int]:
        current_year = datetime.now().year
        start_year = current_year - 5
        start_date = datetime(start_year, 1, 1)
        end_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)

        db_group_format = {
            'postgresql': 'YYYY',
            'mysql': '%Y',
            'sqlite': '%Y'
        }.get(self.db.bind.name, '%Y')

        raw_data = self._get_conversation_counts_by_period(db_group_format, start_date, end_date, client_id)

        result = {}
        for year in range(start_year, current_year + 1):
            year_key = str(year)
            result[year_key] = raw_data.get(year_key, 0)

        return result
    
    def _get_escalation_condition(self):
        """
        Mengembalikan kondisi SQLAlchemy untuk mengidentifikasi eskalasi.
        Berdasarkan kemunculan 'INSERT INTO ai.dt_customer_feedback' di agent_tools_call.
        """
        return exists(
            select(1)
            .select_from(
                func.unnest(Chat.agent_tools_call).alias("tool")
            )
            .where(
                or_(
                    column("tool", type_=Text).ilike('%INSERT INTO ai.dt_customer_feedback%'),
                    column("tool", type_=Text).ilike('%INSERT INTO ai.customer_feedback%')
                )
            )
        )

    def _get_escalation_counts_by_period(self, group_format: str, start_date: datetime, end_date: datetime, client_id: UUID) -> Dict[str, int]:
        """
        Helper private untuk mendapatkan jumlah eskalasi berdasarkan format grup periode.
        Digunakan oleh metode weekly, monthly, yearly.
        """
        try:
            if self.db.bind.name == 'postgresql':
                period_expr = func.to_char(Chat.created_at, group_format)
            else:  
                period_expr = func.strftime(group_format, Chat.created_at)

            query_results = self.db.query(
                period_expr.label("period"),
                func.count(distinct(Chat.id)).label("total_escalations")
            ).filter(
                Chat.created_at >= start_date,
                Chat.created_at <= end_date,
                Chat.client_id == client_id,
                self._get_escalation_condition()  
            ).group_by("period").all()  

            result_dict = {row.period: row.total_escalations for row in query_results}
            return result_dict
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error getting escalation counts by period: {e}", exc_info=True)
            raise DatabaseException("GET_ESCALATION_COUNT_BY_PERIOD", "Failed to getting escalation counts by period.")

    def get_weekly_escalation_count(self, client_id: UUID) -> Dict[str, int]:
        """
        Mendapatkan data eskalasi per minggu (ISO Week),
        dengan kunci berupa tanggal Minggu terakhir dari minggu tersebut (YYYY-MM-DD).
        """
        final_weekly_stats: Dict[str, int] = {}
        today = datetime.now()

        start_date_for_query = today + relativedelta(weeks=-12, weekday=SU(-1))  
        end_date_for_query = today.replace(hour=23, minute=59, second=59, microsecond=999999)

        db_group_format = 'IYYY-IW'

        raw_data_iso_week = self._get_escalation_counts_by_period(db_group_format, start_date_for_query,
                                                                  end_date_for_query, client_id)
        
        first_sunday_in_range = today + relativedelta(weeks=-11, weekday=SU)  

        for i in range(12):  
            current_sunday = first_sunday_in_range + timedelta(weeks=i)

            iso_year, iso_week, _ = current_sunday.isocalendar()

            week_key_iso = f"{iso_year}-{iso_week:02d}"

            final_date_key = current_sunday.strftime('%Y-%m-%d')

            final_weekly_stats[final_date_key] = raw_data_iso_week.get(week_key_iso, 0)

        sorted_keys = sorted(final_weekly_stats.keys())
        return {k: final_weekly_stats[k] for k in sorted_keys}

    def get_monthly_escalation_count(self, client_id: UUID) -> Dict[str, int]:
        today = datetime.now()
        start_date = (today.replace(day=1) - timedelta(days=365)).replace(day=1)
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)

        db_group_format = {
            'postgresql': 'YYYY-MM',
            'mysql': '%Y-%m',
            'sqlite': '%Y-%m'
        }.get(self.db.bind.name, '%Y-%m')
        
        raw_data = self._get_escalation_counts_by_period(db_group_format, start_date, end_date, client_id)
        
        logger.debug(f"Raw escalation data from DB: {raw_data}")
        
        result = {}
        for i in range(12):
            month_date = (today.replace(day=1) - timedelta(days=30 * (11 - i)))
            accurate_month = (today.month - 11 + i - 1) % 12 + 1
            accurate_year = today.year + ((today.month - 11 + i - 1) // 12)
            month_date = datetime(accurate_year, accurate_month, 1)
            month_key = month_date.strftime('%Y-%m')
            result[month_key] = raw_data.get(month_key, 0)

        return result

    def get_yearly_escalation_count(self, client_id: UUID) -> Dict[str, int]:
        final_yearly_stats: Dict[str, int] = {}
        current_year = datetime.now().year

        start_date_for_query = datetime(current_year - 5, 1, 1)
        end_date_for_query = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)

        db_group_format = 'YYYY'

        raw_data = self._get_escalation_counts_by_period(db_group_format, start_date_for_query, end_date_for_query, client_id)

        for year in range(current_year - 5, current_year + 1):
            year_key = str(year)
            final_yearly_stats[year_key] = raw_data.get(year_key, 0)

        return final_yearly_stats

    def get_all_chat_history(self, offset: int, limit: int, client_id: UUID, search: Optional[str] = None) -> PaginatedChatHistoryResponse:
        try:
            logger.info(f"Fetching chat history. offset={offset}, limit={limit}, search='{search}'")
            query = self.db.query(Chat).filter(Chat.client_id == client_id)

            if search:
                search_filter = f"%{search.lower()}%"
                query = query.filter(
                    or_(
                        func.lower(Chat.message).like(search_filter),
                        func.lower(cast(Chat.sender_id, String)).like(search_filter)
                    )
                )

            total_count = query.count()

            chat_history = query.order_by(desc(Chat.created_at))\
                                .offset(offset)\
                                .limit(limit)\
                                .all()

            return PaginatedChatHistoryResponse(
                total=total_count,
                data=[ChatHistoryResponse.from_orm(chat) for chat in chat_history]
            )
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy error: {e}", exc_info=True)
            raise DatabaseException("GET_ALL_CHAT_HISTORY", "Failed to getting all chat history.")

    def get_categories_by_frequency(self, client_id: UUID) -> List[Dict[str, Any]]:
        """
        Mengambil kategori respons agent dan menghitung frekuensinya,
        diurutkan dari yang terbanyak. Cocok untuk dashboard.

        Returns:
            List of dictionaries, each containing 'category' and 'count'.
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info("Getting categories by frequency.")
            
            category_counts = self.db.query(
                Chat.agent_response_category,
                func.count(Chat.agent_response_category).label('count')
            ).filter(
                Chat.client_id == client_id,
                Chat.agent_response_category.isnot(None),
                Chat.agent_response_category != ''
            ).group_by(
                Chat.agent_response_category
            ).order_by(
                desc('count') 
            ).all()

            result = [{"category": cat, "frequency": count} for cat, count in category_counts]
            logger.info(f"Fetched {len(result)} categories.")
            return result
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error getting categories by frequency: {e}", exc_info=True)
            raise DatabaseException("GET_CATEGORIES_BY_FREQ", "Failed to getting categories by frequency.")
        
    def get_user_chat_history_by_user_id(self, user_id: UUID, offset: int, limit: int, client_id: UUID) -> dict:
        """
        Mengambil riwayat chat untuk user spesifik berdasarkan user_id, dengan pagination.

        Args:
            user_id: UUID dari user.
            offset: Jumlah item yang akan dilewati.
            limit: Jumlah item per halaman.

        Returns:
            List of Chat objects terkait user_id. Mengembalikan list kosong jika user_id tidak ditemukan
            atau tidak memiliki riwayat chat.
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info(f"Fetching chat history for room {user_id} with offset={offset}, limit={limit}.")

            subquery = (
                self.db.query(Chat.room_conversation_id)
                .filter(Chat.sender_id == user_id, Chat.client_id == client_id)
                .distinct()
                .subquery()
            )

            user_history = (
                self.db.query(Chat)
                .filter(Chat.room_conversation_id.in_(select(subquery)))
                .order_by(Chat.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            
            user_history.reverse()
            
            total_count = (
                self.db.query(Chat)
                .filter(
                    Chat.room_conversation_id.in_(select(subquery)),
                    Chat.client_id == client_id
                )
                .count()
            )

            logger.info(f"Successfully fetched {len(user_history)} chat entries for room {user_id}.")
            
            return {
                "total": total_count,
                "data": user_history
            }

        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error fetching chat history for room {user_id}: {e}", exc_info=True)
            raise DatabaseException("GET_CATEGORIES_BY_FREQ", "Error fetching chat history by user id.")
        except Exception as e:
            logger.error(f"Unexpected Error fetching chat history for room {user_id}: {e}", exc_info=True)
            raise DatabaseException("GET_CATEGORIES_BY_FREQ", "Error fetching chat history by user id.")
        
    def get_user_chat_history_by_room_id(self, room_id: UUID, offset: int, limit: int, client_id: UUID) -> dict:
        """
        Mengambil riwayat chat untuk user spesifik berdasarkan room_id, dengan pagination.

        Args:
            room_id: UUID dari room.
            offset: Jumlah item yang akan dilewati.
            limit: Jumlah item per halaman.

        Returns:
            Dict dengan user_id, total, dan history.
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info(f"Fetching chat history for room {room_id} with offset={offset}, limit={limit}.")

            user_member = self.db.query(Member.user_id)\
                .filter(
                    Member.room_conversation_id == room_id,
                    Member.role == 'user',
                    Member.client_id == client_id
                )\
                .first()

            if not user_member:
                logger.warning(f"Tidak ditemukan member dengan role='user' di room {room_id}")
                return {
                    "user_id": None,
                    "total": 0,
                    "history": []
                }

            user_id = user_member.user_id

            total_count = self.db.query(Chat)\
                .filter(Chat.room_conversation_id == room_id,
                        Chat.client_id == client_id,
                        Chat.sender_id == user_id)\
                .count()

            history = self.db.query(Chat)\
                .filter(Chat.room_conversation_id == room_id, 
                        Chat.client_id == client_id)\
                .order_by(Chat.created_at.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
            
            history.reverse()

            logger.info(f"Successfully fetched {len(history)} of {total_count} chat entries for room {room_id}.")

            return {
                "user_id": user_id,
                "total_count": total_count,
                "history": history
            }
        
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error fetching chat history for room {room_id}: {e}", exc_info=True)
            raise DatabaseException("GET_CATEGORIES_BY_FREQ", "Error fetching chat history by room.")
        
        except Exception as e:
            logger.error(f"Unexpected Error fetching chat history for room {room_id}: {e}", exc_info=True)
            raise DatabaseException("GET_CATEGORIES_BY_FREQ", "Error fetching chat history by room.")
        
    def get_total_tokens_used(self, client_id: UUID) -> float:
        """
        Menghitung total jumlah token yang digunakan oleh client tertentu
        dengan menjumlahkan kolom 'agent_total_tokens' dari tabel Chat
        yang terhubung dengan RoomConversation milik client tersebut.
        """
        try:
            logger.info(f"[SERVICE][TOKEN] Calculating total tokens used for client_id={client_id}.")

            total_tokens = (
                self.db.query(
                    func.coalesce(func.sum(cast(Chat.agent_total_tokens, Float)), 0.0)
                )
                .join(RoomConversation, RoomConversation.id == Chat.room_conversation_id)
                .filter(RoomConversation.client_id == client_id)
                .scalar()
            )

            result = float(total_tokens) if total_tokens is not None else 0.0
            logger.info(f"[SERVICE][TOKEN] Total tokens used for client {client_id}: {result}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][TOKEN] SQLAlchemy Error calculating total tokens used for client {client_id}: {e}", exc_info=True)
            raise DatabaseException("GET_TOTAL_TOKEN_USED", "Error calculating total tokens used.")
    
    def get_total_conversations(self, client_id: UUID) -> int:
        """
        Menghitung total jumlah percakapan (Chat.id) untuk client tertentu.
        """
        try:
            logger.info(f"Counting total unique conversations for client_id={client_id}")
            
            total_conversations = (
                self.db.query(func.count(distinct(Chat.id)))
                .join(RoomConversation)
                .filter(RoomConversation.client_id == client_id)
                .scalar()
            )

            return total_conversations if total_conversations is not None else 0
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error getting total conversations: {e}", exc_info=True)
            raise DatabaseException("GET_TOTAL_CONVERSATION", "Error calculating total conversations.")

    def get_monthly_conversations(self, client_id: UUID) -> Dict[str, int]:
        """
        Mengambil total percakapan per bulan untuk client tertentu.
        """
        try:
            logger.info(f"Getting monthly total conversations for client_id={client_id}")
            monthly_conversation_counts_raw = (
                self.db.query(
                    func.to_char(Chat.created_at, 'YYYY-MM').label('month'),
                    func.count(distinct(Chat.id)).label('count')
                )
                .join(RoomConversation, RoomConversation.id == Chat.room_conversation_id)
                .filter(RoomConversation.client_id == client_id)
                .group_by('month')
                .order_by('month')
                .all()
            )

            current_year = datetime.now().year
            current_month = datetime.now().month
            monthly_data = defaultdict(int)

            for i in range(1, current_month + 1):
                month_str = f"{current_year}-{i:02d}"
                monthly_data[month_str] = 0

            for month, count in monthly_conversation_counts_raw:
                if month in monthly_data:
                    monthly_data[month] = count

            sorted_result = dict(sorted(monthly_data.items()))
            logger.info(f"Monthly total conversations: {sorted_result}")
            return sorted_result
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error getting monthly total conversations: {e}", exc_info=True)
            raise DatabaseException("GET_TOTAL_MONTHLY_CONVERSATION", "Error getting monthly total conversations.")

    def get_daily_average_latency_seconds(self, client_id: UUID):
        """
        Mengambil latensi rata-rata harian selama 7 hari terakhir untuk client tertentu.
        """
        try:
            logger.info(f"Getting daily average latency for client_id={client_id}")

            end_date = datetime.combine(datetime.now().date(), datetime.max.time())
            start_date = end_date - timedelta(days=6)

            daily_latency_raw = (
                self.db.query(
                    func.to_char(Chat.created_at, 'YYYY-MM-DD').label('day'),
                    func.avg(func.extract('epoch', Chat.agent_response_latency)).label('avg_latency_seconds')
                )
                .join(RoomConversation, RoomConversation.id == Chat.room_conversation_id)
                .filter(
                    RoomConversation.client_id == client_id,
                    Chat.agent_response_latency.isnot(None),
                    Chat.created_at >= start_date,
                    Chat.created_at <= end_date
                )
                .group_by('day')
                .order_by('day')
                .all()
            )

            daily_data = defaultdict(float)
            for i in range(7):
                day = start_date + timedelta(days=i)
                day_str = day.strftime('%Y-%m-%d')
                daily_data[day_str] = 0.0

            for day, avg_latency_seconds in daily_latency_raw:
                if day in daily_data:
                    daily_data[day] = round(avg_latency_seconds, 2)

            sorted_result = dict(sorted(daily_data.items()))
            logger.info(f"7-day average latency (seconds): {sorted_result}")
            return sorted_result

        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error getting daily average latency in seconds: {e}", exc_info=True)
            raise DatabaseException("GET_AVERAGE_LATENCY", "Error getting daily average latency in seconds.")

    def get_monthly_average_latency_seconds(self, client_id: UUID):
        """
        Mengambil latensi rata-rata bulanan dalam detik (float) untuk client tertentu.
        """
        try:
            logger.info(f"Getting monthly average latency in seconds for client_id={client_id}")
            
            current_year = datetime.now().year
            current_month = datetime.now().month
            monthly_data = defaultdict(float)
            
            monthly_latency_raw = (
                self.db.query(
                    func.to_char(Chat.created_at, 'YYYY-MM').label('month'),
                    func.avg(func.extract('epoch', Chat.agent_response_latency)).label('avg_latency_seconds')
                )
                .join(RoomConversation, RoomConversation.id == Chat.room_conversation_id)
                .filter(
                    RoomConversation.client_id == client_id,
                    Chat.agent_response_latency.isnot(None),
                    func.extract('year', Chat.created_at) == current_year
                )
                .group_by('month')
                .order_by('month')
                .all()
            )

            for i in range(1, current_month + 1):
                month_str = f"{current_year}-{i:02d}"
                monthly_data[month_str] = 0.0

            for month, avg_latency_seconds in monthly_latency_raw:
                if month in monthly_data:
                    monthly_data[month] = round(avg_latency_seconds, 2)

            sorted_result = dict(sorted(monthly_data.items()))
            logger.info(f"Monthly average latency (seconds): {sorted_result}")
            return sorted_result
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error getting monthly average latency in seconds: {e}", exc_info=True)
            raise DatabaseException("GET_MONTHLY_AVERAGE_LATENCY", "Error getting monthly average latency in seconds.")

    def get_escalation_by_month(self, client_id: UUID):
        """
        Menghitung total eskalasi bulanan berdasarkan kemunculan 'INSERT INTO ai.dt_customer_feedback'
        di dalam array 'agent_tools_call' pada tabel 'dt_chats', difilter per client.
        """
        try:
            logger.info(f"Getting monthly escalation count for client_id={client_id}")

            exists_condition = exists(
                select(1)
                .select_from(
                    func.unnest(Chat.agent_tools_call).alias("tool")
                )
                .where(
                    or_(
                        column("tool", type_=Text).ilike('%INSERT INTO ai.dt_customer_feedback%'),
                        column("tool", type_=Text).ilike('%INSERT INTO ai.customer_feedback%')
                    )
                )
            )

            monthly_escalation_raw = (
                self.db.query(
                    func.to_char(Chat.created_at, 'YYYY-MM').label('month'),
                    func.count(Chat.id).label('count')
                )
                .join(RoomConversation, RoomConversation.id == Chat.room_conversation_id)
                .filter(
                    RoomConversation.client_id == client_id,
                    Chat.agent_tools_call.isnot(None),
                    func.cardinality(Chat.agent_tools_call) > 0,
                    exists_condition
                )
                .group_by('month')
                .order_by('month')
                .all()
            )

            now = datetime.now()
            current_year = now.year
            current_month = now.month

            monthly_data = defaultdict(int)
            for i in range(1, current_month + 1):
                month_str = f"{current_year}-{i:02d}"
                monthly_data[month_str] = 0

            for month_db, count_db in monthly_escalation_raw:
                monthly_data[month_db] = count_db

            sorted_result = dict(sorted(monthly_data.items()))
            logger.info(f"Monthly escalation count: {sorted_result}")
            return sorted_result

        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error getting monthly escalation count: {e}", exc_info=True)
            raise DatabaseException("GET_TOTAL_ESCALATION_MONTH", "Error getting monthly escalation count.")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            raise DatabaseException("GET_TOTAL_ESCALATION_MONTH", "Error getting monthly escalation count.")

    def get_monthly_tokens_used(self, client_id: UUID) -> Dict[str, float]:
        """
        Menghitung total jumlah token yang digunakan setiap bulan selama tahun berjalan untuk client tertentu.
        """
        try:
            logger.info(f"Calculating monthly tokens used for client_id={client_id}")
            current_year = datetime.now().year

            month_expr = func.to_char(Chat.created_at, 'YYYY-MM')

            monthly_tokens = (
                self.db.query(
                    month_expr.label('month'),
                    func.sum(Chat.agent_total_tokens).label('total_tokens')
                )
                .join(RoomConversation, RoomConversation.id == Chat.room_conversation_id)
                .filter(
                    RoomConversation.client_id == client_id,
                    extract('year', Chat.created_at) == current_year
                )
                .group_by(month_expr)
                .order_by(month_expr)
                .all()
            )

            monthly_data = defaultdict(float)
            for month_num in range(1, datetime.now().month + 1):
                month_str = f"{current_year}-{month_num:02d}"
                monthly_data[month_str] = 0.0

            for month_year_str, total_tokens in monthly_tokens:
                monthly_data[month_year_str] = total_tokens if total_tokens is not None else 0.0

            sorted_monthly_data = dict(sorted(monthly_data.items()))
            logger.info(f"Monthly tokens used data: {sorted_monthly_data}")
            return sorted_monthly_data

        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error calculating monthly tokens used: {e}", exc_info=True)
            raise DatabaseException("GET_MONTHLY_TOKEN_USED", "Error calculating monthly tokens used.")


def get_chat_history_service(db: Session = Depends(config_db)):
    """
    Dependency untuk mendapatkan instance ChatHistoryService dengan sesi database.
    """
    return ChatHistoryService(db)
