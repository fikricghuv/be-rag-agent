# app/services/chat_history_service.py
import uuid
import logging 
from sqlalchemy.orm import Session
from sqlalchemy import func, select, literal_column, column, extract
from sqlalchemy.sql import select, func, distinct, desc, exists
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError 
from fastapi import Depends 
from typing import List, Dict, Any
from collections import defaultdict
from database.models import Chat, RoomConversation, Member
from core.config_db import config_db
from sqlalchemy import TEXT, Text
from dateutil.relativedelta import relativedelta, SU
from schemas.chat_history_schema import PaginatedChatHistoryResponse, ChatHistoryResponse


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

    def _get_conversation_counts_by_period(self, group_format: str, start_date: datetime, end_date: datetime) -> Dict[
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
                Chat.created_at <= end_date
            ).group_by("period").all()

            return {row.period: row.total_conversations for row in query_results}
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error getting conversation counts by period: {e}", exc_info=True)
            raise e

    def get_conversations_by_week(self) -> Dict[str, int]:
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
                                                                    end_date_for_query)
        first_sunday_in_range = today + relativedelta(weeks=-11, weekday=SU)

        for i in range(12): 
            
            current_sunday = first_sunday_in_range + timedelta(weeks=i)

            iso_year, iso_week, _ = current_sunday.isocalendar()
            week_key_iso = f"{iso_year}-{iso_week:02d}"

            final_date_key = current_sunday.strftime('%Y-%m-%d')

            final_weekly_stats[final_date_key] = raw_data_iso_week.get(week_key_iso, 0)

        sorted_keys = sorted(final_weekly_stats.keys())
        return {k: final_weekly_stats[k] for k in sorted_keys}

    def get_conversations_by_month(self) -> Dict[str, int]:
        today = datetime.now()
        start_date = (today.replace(day=1) - timedelta(days=365)).replace(day=1)
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)

        db_group_format = {
            'postgresql': 'YYYY-MM',
            'mysql': '%Y-%m',
            'sqlite': '%Y-%m'
        }.get(self.db.bind.name, '%Y-%m')

        raw_data = self._get_conversation_counts_by_period(db_group_format, start_date, end_date)

        result = {}
        for i in range(12):
            month_date = (today.replace(day=1) - timedelta(days=30 * (11 - i)))
            accurate_month = (today.month - 11 + i - 1) % 12 + 1
            accurate_year = today.year + ((today.month - 11 + i - 1) // 12)
            month_date = datetime(accurate_year, accurate_month, 1)
            month_key = month_date.strftime('%Y-%m')
            result[month_key] = raw_data.get(month_key, 0)

        return result

    def get_conversations_by_year(self) -> Dict[str, int]:
        current_year = datetime.now().year
        start_year = current_year - 5
        start_date = datetime(start_year, 1, 1)
        end_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)

        db_group_format = {
            'postgresql': 'YYYY',
            'mysql': '%Y',
            'sqlite': '%Y'
        }.get(self.db.bind.name, '%Y')

        raw_data = self._get_conversation_counts_by_period(db_group_format, start_date, end_date)

        result = {}
        for year in range(start_year, current_year + 1):
            year_key = str(year)
            result[year_key] = raw_data.get(year_key, 0)

        return result
    
    def _get_escalation_condition(self):
        """
        Mengembalikan kondisi SQLAlchemy untuk mengidentifikasi eskalasi.
        Berdasarkan kemunculan 'INSERT INTO ai.customer_feedback' di agent_tools_call.
        """
        return exists(
            select(1).select_from(
                func.unnest(Chat.agent_tools_call).alias("tool")
            ).where(
                column("tool", type_=TEXT).ilike('%INSERT INTO ai.customer_feedback%')
            )
        )

    def _get_escalation_counts_by_period(self, group_format: str, start_date: datetime, end_date: datetime) -> Dict[
        str, int]:
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
                self._get_escalation_condition()  
            ).group_by("period").all()  

            result_dict = {row.period: row.total_escalations for row in query_results}
            return result_dict
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error getting escalation counts by period: {e}", exc_info=True)
            raise e

    def get_weekly_escalation_count(self) -> Dict[str, int]:
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
                                                                  end_date_for_query)
        
        first_sunday_in_range = today + relativedelta(weeks=-11, weekday=SU)  

        for i in range(12):  
            current_sunday = first_sunday_in_range + timedelta(weeks=i)

            iso_year, iso_week, _ = current_sunday.isocalendar()

            week_key_iso = f"{iso_year}-{iso_week:02d}"

            final_date_key = current_sunday.strftime('%Y-%m-%d')

            final_weekly_stats[final_date_key] = raw_data_iso_week.get(week_key_iso, 0)

        sorted_keys = sorted(final_weekly_stats.keys())
        return {k: final_weekly_stats[k] for k in sorted_keys}


    def get_monthly_escalation_count(self) -> Dict[str, int]:
        today = datetime.now()
        start_date = (today.replace(day=1) - timedelta(days=365)).replace(day=1)
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)

        db_group_format = {
            'postgresql': 'YYYY-MM',
            'mysql': '%Y-%m',
            'sqlite': '%Y-%m'
        }.get(self.db.bind.name, '%Y-%m')
        
        raw_data = self._get_escalation_counts_by_period(db_group_format, start_date, end_date)
        
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


    def get_yearly_escalation_count(self) -> Dict[str, int]:
        final_yearly_stats: Dict[str, int] = {}
        current_year = datetime.now().year

        start_date_for_query = datetime(current_year - 5, 1, 1)
        end_date_for_query = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)

        db_group_format = 'YYYY'

        raw_data = self._get_escalation_counts_by_period(db_group_format, start_date_for_query, end_date_for_query)

        for year in range(current_year - 5, current_year + 1):
            year_key = str(year)
            final_yearly_stats[year_key] = raw_data.get(year_key, 0)

        return final_yearly_stats
    
    def get_all_chat_history(self, offset: int, limit: int) -> PaginatedChatHistoryResponse:
        """
        Mengambil data Chat dengan pagination dan total count.

        Args:
            offset: Jumlah item yang akan dilewati.
            limit: Jumlah item per halaman.

        Returns:
            Dict dengan keys: 'total' (jumlah semua chat), dan 'data' (list chat).
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info(f"Fetching all chat history from database with offset={offset}, limit={limit}, ordered by created_at DESC.")

            # Hitung total data
            total_count = self.db.query(Chat).count()

            # Ambil data sesuai pagination
            chat_history = self.db.query(Chat)\
                .order_by(desc(Chat.created_at))\
                .offset(offset)\
                .limit(limit)\
                .all()

            logger.info(f"Successfully fetched {len(chat_history)} chat entries out of {total_count} total.")

            return PaginatedChatHistoryResponse(
            total=total_count,
            data=[ChatHistoryResponse.from_orm(chat) for chat in chat_history]
        )
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error fetching all chat history with pagination: {e}", exc_info=True)
            raise e

        
    def get_categories_by_frequency(self) -> List[Dict[str, Any]]:
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
            raise e

    def get_user_chat_history_by_user_id(self, user_id: uuid.UUID, offset: int, limit: int) -> dict:
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
                .filter(Chat.sender_id == user_id)
                .distinct()
                .subquery()
            )

            user_history = (
                self.db.query(Chat)
                .filter(Chat.room_conversation_id.in_(subquery))
                .order_by(Chat.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            
            user_history.reverse()
            
            total_count = (
                self.db.query(Chat)
                .filter(Chat.room_conversation_id.in_(subquery))
                .count()
            )

            logger.info(f"Successfully fetched {len(user_history)} chat entries for room {user_id}.")
            
            return {
                "total": total_count,
                "data": user_history
            }

        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error fetching chat history for room {user_id}: {e}", exc_info=True)
            raise e 
        except Exception as e:
            logger.error(f"Unexpected Error fetching chat history for room {user_id}: {e}", exc_info=True)
            
            raise SQLAlchemyError(f"Unexpected error: {e}")
        
    def get_user_chat_history_by_room_id(self, room_id: uuid.UUID, offset: int, limit: int) -> dict:
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
                    Member.role == 'user'
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

            # Total count tanpa pagination
            total_count = self.db.query(Chat)\
                .filter(Chat.room_conversation_id == room_id)\
                .count()

            # Ambil data dengan offset dan limit
            history = self.db.query(Chat)\
                .filter(Chat.room_conversation_id == room_id)\
                .order_by(Chat.created_at)\
                .offset(offset)\
                .limit(limit)\
                .all()

            logger.info(f"Successfully fetched {len(history)} of {total_count} chat entries for room {room_id}.")

            return {
                "user_id": user_id,
                "total_count": total_count,
                "history": history
            }
        
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error fetching chat history for room {room_id}: {e}", exc_info=True)
            raise e 
        
        except Exception as e:
            logger.error(f"Unexpected Error fetching chat history for room {room_id}: {e}", exc_info=True)
            
            raise SQLAlchemyError(f"Unexpected error: {e}")
        
    def get_total_tokens_used(self) -> float:
        """
        Menghitung total jumlah token yang digunakan di seluruh riwayat chat.
        Menjumlahkan kolom 'agent_total_tokens' dari tabel Chat.

        Returns:
            Total jumlah token sebagai integer. Mengembalikan 0 jika tidak ada token atau terjadi kesalahan.
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info("Calculating total tokens used across all chat history.")
            
            total_tokens = self.db.query(func.sum(Chat.agent_total_tokens)).scalar()
            
            result = total_tokens if total_tokens is not None else 0
            logger.info(f"Total tokens used: {result}")
            return result
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error calculating total tokens used: {e}", exc_info=True)
            raise e

    def get_total_conversations(self) -> int:
        """
        Menghitung total jumlah percakapan berdasarkan room_conversation_id di tabel Chat.

        Returns:
            Total count of unique conversations.
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info("Counting total unique conversations.")
            
            total_conversations = self.db.query(func.count(distinct(Chat.id))).scalar()
            logger.info(f"Total unique conversations: {total_conversations}")
            return total_conversations if total_conversations is not None else 0
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error getting total conversations: {e}", exc_info=True)
            raise e
        
    def get_monthly_conversations(self) -> Dict[str, int]:
        """
        Mengambil total percakapan per bulan.
        Percakapan dihitung berdasarkan room_conversation_id unik dari tabel Chat.
        Mengembalikan dictionary dengan format: {'YYYY-MM': count}
        Jika bulan tidak ada data, akan diisi dengan 0.
        """
        try:
            logger.info("Getting monthly total conversations.")
            monthly_conversation_counts_raw = self.db.query(
                func.to_char(Chat.created_at, 'YYYY-MM').label('month'),
                func.count(distinct(Chat.id)).label('count')
            ).group_by('month').order_by('month').all()

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
            raise e
        
    def get_daily_average_latency_seconds(self):
        """
        Mengambil latensi rata-rata harian dalam detik (float).
        Mengembalikan dictionary dengan format: {'YYYY-MM-DD': avg_latency_seconds}
        Jika hari tidak ada data, akan diisi dengan 0.0.
        """
        try:
            logger.info("Getting daily average latency in seconds (float).")
            
            daily_latency_raw = self.db.query(
                func.to_char(Chat.created_at, 'YYYY-MM-DD').label('day'),
                func.avg(func.extract('epoch', Chat.agent_response_latency)).label('avg_latency_seconds')
            ).filter(Chat.agent_response_latency.isnot(None)).group_by('day').order_by('day').all()

            current_date = datetime.now().date()
            daily_data = defaultdict(float) 

            for i in range(1, current_date.day + 1):
                day_str = f"{current_date.year}-{current_date.month:02d}-{i:02d}"
                daily_data[day_str] = 0.0 

            for day, avg_latency_seconds in daily_latency_raw:
                if day in daily_data:
                    daily_data[day] = round(avg_latency_seconds, 2) 

            sorted_result = dict(sorted(daily_data.items()))
            logger.info(f"Daily average latency (seconds): {sorted_result}")
            return sorted_result
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error getting daily average latency in seconds: {e}", exc_info=True)
            raise e

    def get_monthly_average_latency_seconds(self):
        """
        Mengambil latensi rata-rata bulanan dalam detik (float).
        Mengembalikan dictionary dengan format: {'YYYY-MM': avg_latency_seconds}
        Jika bulan tidak ada data, akan diisi dengan 0.0.
        """
        try:
            logger.info("Getting monthly average latency in seconds (float).")
            monthly_latency_raw = self.db.query(
                func.to_char(Chat.created_at, 'YYYY-MM').label('month'),
                func.avg(func.extract('epoch', Chat.agent_response_latency)).label('avg_latency_seconds')
            ).filter(Chat.agent_response_latency.isnot(None)).group_by('month').order_by('month').all()

            current_year = datetime.now().year
            current_month = datetime.now().month
            monthly_data = defaultdict(float)

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
            raise e
        
    def get_escalation_by_month(self):
        """
        Menghitung total eskalasi bulanan berdasarkan kemunculan 'INSERT INTO ai.customer_feedback'
        di dalam elemen array 'agent_tools_call' pada tabel 'chats'.
        Mengembalikan dict: {'YYYY-MM': count}, termasuk bulan di tahun ini yang belum memiliki data.
        """
        try:
            logger.info("Getting monthly escalation count.")

            exists_condition = exists(
                select(1).select_from(
                    func.unnest(Chat.agent_tools_call).alias("tool")
                ).where(
                    column("tool", type_=Text).ilike('%INSERT INTO ai.customer_feedback%')
                )
            )

            monthly_escalation_raw = self.db.query(
                func.to_char(Chat.created_at, 'YYYY-MM').label('month'),
                func.count(Chat.id).label('count')
            ).filter(
                Chat.agent_tools_call.isnot(None),
                func.cardinality(Chat.agent_tools_call) > 0,
                exists_condition
            ).group_by('month').order_by('month').all()

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
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            raise
        
    def get_monthly_tokens_used(self) -> Dict[str, float]:
        """
        Menghitung total jumlah token yang digunakan setiap bulan selama tahun berjalan.
        Menjumlahkan kolom 'agent_total_tokens' dari tabel Chat, dikelompokkan berdasarkan bulan.
        """
        try:
            logger.info("Calculating monthly tokens used for the current year.")
            current_year = datetime.now().year

            month_expr = func.to_char(Chat.created_at, 'YYYY-MM')

            monthly_tokens = self.db.query(
                month_expr.label('month'),
                func.sum(Chat.agent_total_tokens).label('total_tokens')
            ).filter(
                extract('year', Chat.created_at) == current_year
            ).group_by(
                month_expr
            ).order_by(
                month_expr
            ).all()

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
            raise

def get_chat_history_service(db: Session = Depends(config_db)):
    """
    Dependency untuk mendapatkan instance ChatHistoryService dengan sesi database.
    """
    return ChatHistoryService(db)
