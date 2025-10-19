from datetime import datetime
from app.services.otp_service import send_email_notification


class EmailService:
    """Service for sending address resolver related emails"""
    
    async def send_address_created_email(self, email: str, name: str, dari_address: str) -> bool:
        """Send email when DARI address is created"""
        subject = "Your DARI Address Has Been Created Successfully"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">DARI Wallet</h1>
                    <p style="color: white; margin: 10px 0 0 0; font-size: 16px;">Decentralized Address Resolver Interface</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                    <h2 style="color: #495057; margin-top: 0;">🎉 Congratulations, {name}!</h2>
                    
                    <p style="font-size: 16px; margin: 20px 0;">
                        Your DARI address has been created successfully! You can now receive transactions using your easy-to-remember address.
                    </p>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; border: 2px solid #28a745; text-align: center; margin: 25px 0;">
                        <h3 style="color: #28a745; margin-top: 0;">Your DARI Address</h3>
                        <p style="font-size: 24px; font-weight: bold; color: #495057; margin: 10px 0; font-family: 'Courier New', monospace;">
                            {dari_address}
                        </p>
                    </div>
                    
                    <h3 style="color: #495057;">What's Next?</h3>
                    <ul style="font-size: 16px; padding-left: 20px;">
                        <li>Share your DARI address with others to receive payments</li>
                        <li>Use it instead of your long wallet address</li>
                        <li>Update it anytime from your wallet settings</li>
                    </ul>
                    
                    <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin-top: 25px;">
                        <p style="margin: 0; font-size: 14px; color: #1565c0;">
                            <strong>💡 Tip:</strong> Your DARI address is linked to your wallet address and can be used for all supported tokens (USDC, USDT, MATIC).
                        </p>
                    </div>
                    
                    <p style="margin-top: 30px; font-size: 14px; color: #6c757d;">
                        If you have any questions, please contact our support team.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await send_email_notification(email, subject, body, is_html=True)
    
    async def send_address_updated_email(self, email: str, name: str, old_address: str, new_address: str) -> bool:
        """Send email when DARI address is updated"""
        subject = "Your DARI Address Has Been Updated"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">DARI Wallet</h1>
                    <p style="color: white; margin: 10px 0 0 0; font-size: 16px;">Decentralized Address Resolver Interface</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                    <h2 style="color: #495057; margin-top: 0;">📝 Address Updated, {name}!</h2>
                    
                    <p style="font-size: 16px; margin: 20px 0;">
                        Your DARI address has been successfully updated. Here are the details:
                    </p>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6; margin: 25px 0;">
                        <div style="margin-bottom: 20px;">
                            <h4 style="color: #dc3545; margin: 0 0 10px 0;">Old Address</h4>
                            <p style="font-size: 18px; color: #6c757d; margin: 0; font-family: 'Courier New', monospace; text-decoration: line-through;">
                                {old_address}
                            </p>
                        </div>
                        
                        <div>
                            <h4 style="color: #28a745; margin: 0 0 10px 0;">New Address</h4>
                            <p style="font-size: 20px; font-weight: bold; color: #495057; margin: 0; font-family: 'Courier New', monospace;">
                                {new_address}
                            </p>
                        </div>
                    </div>
                    
                    <div style="background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107; margin: 25px 0;">
                        <p style="margin: 0; font-size: 14px; color: #856404;">
                            <strong>⚠️ Important:</strong> Please update your DARI address wherever you've shared it. The old address is no longer active.
                        </p>
                    </div>
                    
                    <h3 style="color: #495057;">What This Means:</h3>
                    <ul style="font-size: 16px; padding-left: 20px;">
                        <li>Your old DARI address is no longer valid</li>
                        <li>All future transactions should use your new address</li>
                        <li>Your wallet address remains the same</li>
                    </ul>
                    
                    <p style="margin-top: 30px; font-size: 14px; color: #6c757d;">
                        If you didn't make this change, please contact our support team immediately.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await send_email_notification(email, subject, body, is_html=True)
    
    async def send_new_login_alert(self, email: str, user_name: str, ip_address: str, 
                                 user_agent: str, location: str, login_time) -> bool:
        """Send email alert for new device/location login"""
        subject = "New Login Detected - DARI Wallet"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">🔐 New Login Alert</h1>
                    <p style="color: white; margin: 10px 0 0 0; font-size: 16px;">DARI Wallet Security</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                    <p style="margin: 0 0 20px 0; font-size: 16px;">Hello {user_name},</p>
                    
                    <p style="margin: 0 0 20px 0;">We detected a new login to your DARI Wallet account:</p>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6; margin: 20px 0;">
                        <p style="margin: 0 0 10px 0;"><strong>Time:</strong> {login_time.strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                        <p style="margin: 0 0 10px 0;"><strong>IP Address:</strong> {ip_address}</p>
                        <p style="margin: 0 0 10px 0;"><strong>Location:</strong> {location}</p>
                        <p style="margin: 0;"><strong>Device:</strong> {user_agent[:100]}...</p>
                    </div>
                    
                    <p style="margin: 20px 0;">If this was you, you can safely ignore this email. If you don't recognize this activity, please:</p>
                    
                    <ul style="margin: 10px 0 20px 20px;">
                        <li>Change your password immediately</li>
                        <li>Review your account activity</li>
                        <li>Contact our support team</li>
                    </ul>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <p style="margin: 0; font-size: 14px; color: #6c757d;">
                            This is an automated security alert from DARI Wallet.<br>
                            If you have any concerns, please contact our support team.
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await send_email_notification(email, subject, body, is_html=True)
    
    async def send_suspicious_login_alert(self, email: str, user_name: str, ip_address: str, 
                                        user_agent: str, location: str, login_time) -> bool:
        """Send email alert for suspicious login activity"""
        subject = "⚠️ SUSPICIOUS LOGIN DETECTED - DARI Wallet"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">⚠️ Suspicious Activity</h1>
                    <p style="color: white; margin: 10px 0 0 0; font-size: 16px;">DARI Wallet Security Alert</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                    <p style="margin: 0 0 20px 0; font-size: 16px;">Hello {user_name},</p>
                    
                    <div style="background: #fff3cd; border: 1px solid #ffeeba; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="margin: 0; color: #856404;"><strong>⚠️ SECURITY ALERT:</strong> We detected suspicious login activity on your account.</p>
                    </div>
                    
                    <p style="margin: 0 0 20px 0;">Suspicious login details:</p>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6; margin: 20px 0; border-left: 4px solid #dc3545;">
                        <p style="margin: 0 0 10px 0;"><strong>Time:</strong> {login_time.strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                        <p style="margin: 0 0 10px 0;"><strong>IP Address:</strong> {ip_address}</p>
                        <p style="margin: 0 0 10px 0;"><strong>Location:</strong> {location}</p>
                        <p style="margin: 0;"><strong>Device:</strong> {user_agent[:100]}...</p>
                    </div>
                    
                    <div style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="margin: 0 0 10px 0; color: #721c24;"><strong>IMMEDIATE ACTION REQUIRED:</strong></p>
                        <ul style="margin: 0; color: #721c24;">
                            <li>Change your password NOW</li>
                            <li>Enable 2FA if not already enabled</li>
                            <li>Review all account activity</li>
                            <li>Contact support immediately</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <p style="margin: 0; font-size: 14px; color: #6c757d;">
                            This is an automated security alert from DARI Wallet.<br>
                            <strong>Do not ignore this message if you did not authorize this login.</strong>
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await send_email_notification(email, subject, body, is_html=True)
    
    async def send_security_alert(self, ip_address: str, user_agent: str, 
                                failed_attempts: int, time_window: str) -> bool:
        """Send security alert to admin for multiple failed login attempts"""
        from app.core.config import settings
        admin_email = settings.ADMIN_EMAIL
        
        subject = f"🚨 Security Alert: {failed_attempts} Failed Login Attempts"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">🚨 Security Alert</h1>
                    <p style="color: white; margin: 10px 0 0 0; font-size: 16px;">DARI Wallet Admin Alert</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                    <p style="margin: 0 0 20px 0; font-size: 16px;">Admin Alert,</p>
                    
                    <div style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="margin: 0; color: #721c24;"><strong>🚨 BRUTE FORCE ATTACK DETECTED</strong></p>
                    </div>
                    
                    <p style="margin: 0 0 20px 0;">Multiple failed login attempts detected:</p>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6; margin: 20px 0; border-left: 4px solid #dc3545;">
                        <p style="margin: 0 0 10px 0;"><strong>Failed Attempts:</strong> {failed_attempts}</p>
                        <p style="margin: 0 0 10px 0;"><strong>Time Window:</strong> {time_window}</p>
                        <p style="margin: 0 0 10px 0;"><strong>IP Address:</strong> {ip_address}</p>
                        <p style="margin: 0;"><strong>User Agent:</strong> {user_agent[:150]}...</p>
                    </div>
                    
                    <p style="margin: 20px 0;"><strong>Recommended Actions:</strong></p>
                    <ul style="margin: 10px 0 20px 20px;">
                        <li>Consider blocking the IP address</li>
                        <li>Review security logs</li>
                        <li>Monitor for continued attempts</li>
                        <li>Check if any accounts were compromised</li>
                    </ul>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <p style="margin: 0; font-size: 14px; color: #6c757d;">
                            This is an automated security alert from DARI Wallet.<br>
                            Generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await send_email_notification(admin_email, subject, body, is_html=True)
    
    async def send_transaction_sent_email(
        self, 
        email: str, 
        name: str, 
        amount: str, 
        token: str, 
        to_address: str, 
        transaction_hash: str,
        amount_in_user_currency: str = None,
        user_currency: str = "USD"
    ) -> bool:
        """Send email when user sends a transaction"""
        subject = f"💸 Transaction Sent - {amount} {token}"
        
        # Format amount display
        amount_display = f"{amount} {token}"
        if amount_in_user_currency and user_currency != "USD":
            amount_display += f" (≈ {amount_in_user_currency} {user_currency})"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">DARI Wallet</h1>
                    <p style="color: white; margin: 10px 0 0 0; font-size: 16px;">Transaction Confirmation</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                    <h2 style="color: #495057; margin-top: 0;">💸 Transaction Sent Successfully</h2>
                    
                    <p style="font-size: 16px; margin: 20px 0;">
                        Hi {name}, your transaction has been sent successfully!
                    </p>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6; margin: 25px 0;">
                        <h3 style="color: #495057; margin-top: 0;">Transaction Details</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #6c757d;">Amount:</td>
                                <td style="padding: 8px 0; color: #495057;">{amount_display}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #6c757d;">To:</td>
                                <td style="padding: 8px 0; color: #495057; word-break: break-all;">{to_address}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #6c757d;">Transaction Hash:</td>
                                <td style="padding: 8px 0; color: #495057; word-break: break-all; font-family: monospace; font-size: 12px;">{transaction_hash}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #6c757d;">Time:</td>
                                <td style="padding: 8px 0; color: #495057;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="background: #d4edda; padding: 15px; border-radius: 8px; margin-top: 25px; border: 1px solid #c3e6cb;">
                        <p style="margin: 0; font-size: 14px; color: #155724;">
                            <strong>✅ Status:</strong> Transaction confirmed on the blockchain
                        </p>
                    </div>
                    
                    <p style="margin-top: 30px; font-size: 14px; color: #6c757d;">
                        You can view this transaction on the blockchain explorer using the transaction hash above.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await send_email_notification(email, subject, body, is_html=True)
    
    async def send_transaction_received_email(
        self, 
        email: str, 
        name: str, 
        amount: str, 
        token: str, 
        from_address: str, 
        transaction_hash: str,
        amount_in_user_currency: str = None,
        user_currency: str = "USD"
    ) -> bool:
        """Send email when user receives a transaction"""
        subject = f"💰 Payment Received - {amount} {token}"
        
        # Format amount display
        amount_display = f"{amount} {token}"
        if amount_in_user_currency and user_currency != "USD":
            amount_display += f" (≈ {amount_in_user_currency} {user_currency})"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">DARI Wallet</h1>
                    <p style="color: white; margin: 10px 0 0 0; font-size: 16px;">Payment Received</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                    <h2 style="color: #495057; margin-top: 0;">💰 Payment Received!</h2>
                    
                    <p style="font-size: 16px; margin: 20px 0;">
                        Great news {name}! You've received a new payment.
                    </p>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; border: 2px solid #28a745; margin: 25px 0;">
                        <h3 style="color: #28a745; margin-top: 0;">Payment Details</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #6c757d;">Amount:</td>
                                <td style="padding: 8px 0; color: #495057; font-size: 18px; font-weight: bold;">{amount_display}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #6c757d;">From:</td>
                                <td style="padding: 8px 0; color: #495057; word-break: break-all;">{from_address}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #6c757d;">Transaction Hash:</td>
                                <td style="padding: 8px 0; color: #495057; word-break: break-all; font-family: monospace; font-size: 12px;">{transaction_hash}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #6c757d;">Time:</td>
                                <td style="padding: 8px 0; color: #495057;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="background: #d4edda; padding: 15px; border-radius: 8px; margin-top: 25px; border: 1px solid #c3e6cb;">
                        <p style="margin: 0; font-size: 14px; color: #155724;">
                            <strong>✅ Status:</strong> Payment confirmed and available in your wallet
                        </p>
                    </div>
                    
                    <p style="margin-top: 30px; font-size: 14px; color: #6c757d;">
                        The funds are now available in your wallet. You can view this transaction on the blockchain explorer using the transaction hash above.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await send_email_notification(email, subject, body, is_html=True)
    
    async def send_transaction_failed_email(
        self, 
        email: str, 
        name: str, 
        amount: str, 
        token: str, 
        to_address: str, 
        error_message: str = None
    ) -> bool:
        """Send email when user's transaction fails"""
        subject = f"❌ Transaction Failed - {amount} {token}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">DARI Wallet</h1>
                    <p style="color: white; margin: 10px 0 0 0; font-size: 16px;">Transaction Failed</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                    <h2 style="color: #495057; margin-top: 0;">❌ Transaction Failed</h2>
                    
                    <p style="font-size: 16px; margin: 20px 0;">
                        Hi {name}, unfortunately your transaction could not be completed.
                    </p>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; border: 2px solid #dc3545; margin: 25px 0;">
                        <h3 style="color: #dc3545; margin-top: 0;">Transaction Details</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #6c757d;">Amount:</td>
                                <td style="padding: 8px 0; color: #495057;">{amount} {token}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #6c757d;">To:</td>
                                <td style="padding: 8px 0; color: #495057; word-break: break-all;">{to_address}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #6c757d;">Time:</td>
                                <td style="padding: 8px 0; color: #495057;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="background: #f8d7da; padding: 15px; border-radius: 8px; margin-top: 25px; border: 1px solid #f5c6cb;">
                        <p style="margin: 0; font-size: 14px; color: #721c24;">
                            <strong>❌ Status:</strong> Transaction failed
                            {f"<br><strong>Reason:</strong> {error_message}" if error_message else ""}
                        </p>
                    </div>
                    
                    <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin-top: 25px; border: 1px solid #ffeaa7;">
                        <p style="margin: 0; font-size: 14px; color: #856404;">
                            <strong>💡 What to do next:</strong><br>
                            • Check your wallet balance and gas fees<br>
                            • Verify the recipient address is correct<br>
                            • Try the transaction again<br>
                            • Contact support if the issue persists
                        </p>
                    </div>
                    
                    <p style="margin-top: 30px; font-size: 14px; color: #6c757d;">
                        No funds have been deducted from your wallet. If you need assistance, please contact our support team.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await send_email_notification(email, subject, body, is_html=True)


# Create a singleton instance
email_service = EmailService()
