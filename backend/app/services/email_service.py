"""Email Service."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from datetime import datetime

from app.config import get_settings

settings = get_settings()


class EmailService:
    """Service for sending emails."""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.email_from = settings.EMAIL_FROM or settings.SMTP_USER

    @property
    def is_configured(self) -> bool:
        """Check if email is configured."""
        return all([self.smtp_host, self.smtp_user, self.smtp_password])

    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
    ) -> bool:
        """Send an email."""
        if not self.is_configured:
            print("Email not configured, skipping email send")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.email_from
            msg["To"] = ", ".join(to_emails)

            # Add plain text body
            msg.attach(MIMEText(body, "plain"))

            # Add HTML body if provided
            if html_body:
                msg.attach(MIMEText(html_body, "html"))

            # Connect and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.email_from, to_emails, msg.as_string())

            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    def send_test_report(
        self,
        to_emails: List[str],
        task_name: str,
        task_type: str,
        status: str,
        summary: dict,
        message: Optional[str] = None,
    ) -> bool:
        """Send a test report email."""
        # Determine status color
        status_color = "#28a745" if status == "success" else "#dc3545"
        status_text = "成功" if status == "success" else "失败"

        # Build HTML email
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #007bff; color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f9f9f9; padding: 20px; }}
                .status {{ display: inline-block; padding: 5px 15px; border-radius: 3px; color: white; font-weight: bold; }}
                .summary {{ margin-top: 20px; }}
                .summary table {{ width: 100%; border-collapse: collapse; }}
                .summary td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
                .summary td:first-child {{ font-weight: bold; width: 150px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>MirrorGate 测试报告</h1>
                </div>
                <div class="content">
                    <p>您好，</p>
                    <p>测试任务 <strong>{task_name}</strong> 已完成执行。</p>

                    <p>
                        执行状态：
                        <span class="status" style="background-color: {status_color}">{status_text}</span>
                    </p>

                    <div class="summary">
                        <h3>执行摘要</h3>
                        <table>
                            <tr>
                                <td>任务名称</td>
                                <td>{task_name}</td>
                            </tr>
                            <tr>
                                <td>任务类型</td>
                                <td>{task_type}</td>
                            </tr>
                            <tr>
                                <td>执行状态</td>
                                <td style="color: {status_color}">{status_text}</td>
                            </tr>
                            <tr>
                                <td>总用例数</td>
                                <td>{summary.get('total', 0)}</td>
                            </tr>
                            <tr>
                                <td>通过数</td>
                                <td style="color: #28a745">{summary.get('passed', 0)}</td>
                            </tr>
                            <tr>
                                <td>失败数</td>
                                <td style="color: #dc3545">{summary.get('failed', 0)}</td>
                            </tr>
                            <tr>
                                <td>执行时间</td>
                                <td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                            </tr>
                        </table>
                    </div>

                    {f'<p><strong>备注：</strong>{message}</p>' if message else ''}

                    <p>请登录 MirrorGate 查看详细报告。</p>
                </div>
                <div class="footer">
                    <p>此邮件由 MirrorGate 自动发送，请勿回复。</p>
                    <p>&copy; {datetime.now().year} MirrorGate</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Plain text version
        plain_body = f"""
MirrorGate 测试报告

任务名称: {task_name}
任务类型: {task_type}
执行状态: {status_text}
总用例数: {summary.get('total', 0)}
通过数: {summary.get('passed', 0)}
失败数: {summary.get('failed', 0)}
执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'备注: ' + message if message else ''}

请登录 MirrorGate 查看详细报告。
        """.strip()

        subject = f"[MirrorGate] 测试报告: {task_name} - {status_text}"

        return self.send_email(to_emails, subject, plain_body, html_body)


# Global email service instance
email_service = EmailService()
