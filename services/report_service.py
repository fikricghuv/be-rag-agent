import logging 
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status, Depends 
from fastapi.responses import StreamingResponse
import io
import csv
from core.config_db import config_db
from sqlalchemy import text
from io import BytesIO
import pandas as pd
from exceptions.custom_exceptions import DatabaseException, ServiceException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def _remove_timezone(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in df.select_dtypes(include=["datetimetz"]).columns:
            df[col] = df[col].dt.tz_localize(None)
        return df

    def report_csv(self, report_type: str, start_date: str, end_date: str) -> StreamingResponse:
        try:
            logger.info(f"[SERVICE][REPORT] Generating report: {report_type} from {start_date} to {end_date}")
            buffer = io.StringIO()
            writer = csv.writer(buffer)

            if report_type == "CUSTOMER_FEEDBACK":
                query = text("""
                    SELECT 
                        feedback_from_customer, sentiment, potential_actions, keyword_issue,
                        category, product_name, email_user, created_at
                    FROM ai.customer_feedback
                    WHERE created_at BETWEEN :start_date AND :end_date
                    ORDER BY created_at ASC
                """)
                result = self.db.execute(query, {"start_date": start_date, "end_date": end_date})
                writer.writerow([f"Report: Customer Feedback"])
                writer.writerow([f"Date Range: {start_date} to {end_date}"])
                writer.writerow([])
                writer.writerow([
                    "Feedback", "Sentiment", "Potential Actions", "Keyword Issue",
                    "Category", "Product Name", "Email", "Created At"
                ])
                for row in result:
                    writer.writerow(list(row))

            elif report_type == "CHAT_HISTORY":
                query = text("""
                    SELECT room_conversation_id, sender_id, message, role, created_at
                    FROM ai.chats
                    WHERE created_at BETWEEN :start_date AND :end_date
                    ORDER BY created_at ASC
                """)
                result = self.db.execute(query, {"start_date": start_date, "end_date": end_date})
                writer.writerow([f"Report: Chat History"])
                writer.writerow([f"Date Range: {start_date} to {end_date}"])
                writer.writerow([])
                writer.writerow(["Room Conversation ID", "Sender ID", "Message", "Role", "Created At"])
                for row in result:
                    writer.writerow(list(row))

            elif report_type == "CUSTOMER_PROFILE":
                query = text("""
                    SELECT full_name, email, phone_number,
                           customer_type, registration_date, last_activity_at, address,
                           city, country, is_active, created_at, updated_at
                    FROM ai.customers
                    WHERE created_at BETWEEN :start_date AND :end_date
                    ORDER BY created_at ASC
                """)
                result = self.db.execute(query, {"start_date": start_date, "end_date": end_date})
                writer.writerow([f"Report: Customer Profile"])
                writer.writerow([f"Date Range: {start_date} to {end_date}"])
                writer.writerow([])
                writer.writerow([
                    "Full Name", "Email", "Phone Number",
                    "Customer Type", "Registration Date", "Last Activity", "Address",
                    "City", "Country", "Is Active", "Created At", "Updated At"
                ])
                for row in result:
                    writer.writerow(list(row))

            elif report_type == "MOST_QUESTION":
                query = text("""
                    SELECT agent_response_category, COUNT(*) AS count
                    FROM ai.chats
                    WHERE agent_response_category IS NOT NULL AND agent_response_category != ''
                          AND created_at BETWEEN :start_date AND :end_date
                    GROUP BY agent_response_category
                    ORDER BY count DESC
                """)
                result = self.db.execute(query, {"start_date": start_date, "end_date": end_date})
                writer.writerow([f"Report: Category Frequency"])
                writer.writerow([f"Date Range: {start_date} to {end_date}"])
                writer.writerow([])
                writer.writerow(["Category", "Frequency"])
                for row in result:
                    writer.writerow(list(row))

            elif report_type == "CUSTOMER_INTERACTION":
                query = text("""
                    SELECT id, conversation_id, customer_id, start_time, end_time, duration_seconds,
                           channel, initial_query, total_messages, is_handoff_to_agent,
                           agent_id, agent_name, conversation_status, detected_intent, main_topic,
                           keywords_extracted, sentiment_score, product_involved,
                           customer_feedback_id, customer_feedback_score, customer_feedback_comment,
                           feedback_submitted, created_at
                    FROM ai.customer_interactions
                    WHERE created_at BETWEEN :start_date AND :end_date
                    ORDER BY created_at ASC
                """)
                result = self.db.execute(query, {"start_date": start_date, "end_date": end_date})
                writer.writerow([f"Report: Customer Interactions"])
                writer.writerow([f"Date Range: {start_date} to {end_date}"])
                writer.writerow([])
                writer.writerow([
                    "ID", "Conversation ID", "Customer ID", "Start Time", "End Time", "Duration (s)",
                    "Channel", "Initial Query", "Total Messages", "Is Handoff",
                    "Agent ID", "Agent Name", "Conversation Status", "Detected Intent", "Main Topic",
                    "Keywords Extracted", "Sentiment Score", "Product", "Feedback ID",
                    "Feedback Score", "Feedback Comment", "Feedback Submitted", "Created At"
                ])
                for row in result:
                    row_data = list(row)
                    if isinstance(row_data[15], list):
                        row_data[15] = ", ".join(row_data[15])  # keywords_extracted
                    writer.writerow(row_data)

            elif report_type == "ALL_DATA":
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    def query_to_excel(query_str, sheet_name, label):
                        df = pd.read_sql_query(
                            text(query_str),
                            self.db.bind,
                            params={"start_date": start_date, "end_date": end_date}
                        )
                        df = self._remove_timezone(df)

                        # Tulis dulu ke Excel tanpa header tambahan
                        df.to_excel(writer, sheet_name=sheet_name, startrow=3, index=False)

                        # Tambahkan header di atasnya setelah sheet terbentuk
                        ws = writer.book[sheet_name]
                        ws["A1"] = f"Report: {label}"
                        ws["A2"] = f"Date Range: {start_date} to {end_date}"

                    query_to_excel("""
                        SELECT full_name, email, phone_number,
                           customer_type, registration_date, last_activity_at, address,
                           city, country, is_active, created_at, updated_at
                        FROM ai.customers
                        WHERE created_at BETWEEN :start_date AND :end_date
                        ORDER BY created_at ASC
                    """, "Customer Profile", "Customer Profile")

                    query_to_excel("""
                        SELECT id, conversation_id, customer_id, start_time, end_time, duration_seconds,
                           channel, initial_query, total_messages, is_handoff_to_agent,
                           agent_id, agent_name, conversation_status, detected_intent, main_topic,
                           keywords_extracted, sentiment_score, product_involved,
                           customer_feedback_id, customer_feedback_score, customer_feedback_comment,
                           feedback_submitted, created_at
                        FROM ai.customer_interactions
                        WHERE created_at BETWEEN :start_date AND :end_date
                        ORDER BY created_at ASC
                    """, "Customer Interaction", "Customer Interaction")

                    query_to_excel("""
                        SELECT agent_response_category, COUNT(*) AS count
                        FROM ai.chats
                        WHERE agent_response_category IS NOT NULL AND agent_response_category != ''
                            AND created_at BETWEEN :start_date AND :end_date
                        GROUP BY agent_response_category
                        ORDER BY count DESC
                    """, "Most Question", "Most Question (Top Initial Queries)")

                    query_to_excel("""
                        SELECT 
                            feedback_from_customer, sentiment, potential_actions, keyword_issue,
                            category, product_name, email_user, created_at
                        FROM ai.customer_feedback
                        WHERE created_at BETWEEN :start_date AND :end_date
                        ORDER BY created_at ASC
                    """, "Customer Feedback", "Customer Feedback")

                    query_to_excel("""
                        SELECT id, room_conversation_id, sender_id, message, role,
                            agent_response_category, created_at
                        FROM ai.chats
                        WHERE created_at BETWEEN :start_date AND :end_date
                        ORDER BY created_at ASC
                    """, "Chat History", "Chat History")

                output.seek(0)
                filename = f"{report_type.lower()}_{start_date}_to_{end_date}.xlsx"
                return StreamingResponse(
                    output,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f"attachment; filename={filename}"}
                )

            else:
                raise HTTPException(status_code=400, detail=f"Unsupported report type: {report_type}")

            buffer.seek(0)
            return StreamingResponse(
                iter([buffer.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={report_type.lower()}_{start_date}_to_{end_date}.csv"}
            )

        except ServiceException as e:
                self.db.rollback()
                raise
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"[SERVICE][REPORT] DB error: {e}", exc_info=True)
            raise DatabaseException(code="DB_REPORT_ERROR", message="Database error during report generation.")
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"[SERVICE][REPORT] Unexpected error: {e}", exc_info=True)
            raise ServiceException(code="UNEXPECTED_REPORT", message=f"Unexpected error: {str(e)}")


def get_report_service(db: Session = Depends(config_db)):
    return ReportService(db)
