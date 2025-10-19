"""
SMTP Connection Test Script
Test your email configuration before deploying to Render
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys

def test_smtp_ssl(host, port, username, password, from_email, to_email):
    """Test SMTP with SSL (port 465)"""
    print(f"\n{'='*60}")
    print(f"Testing SMTP_SSL: {host}:{port}")
    print(f"{'='*60}")
    
    try:
        print("1. Connecting to SMTP server...")
        server = smtplib.SMTP_SSL(host, port, timeout=30)
        print("   ✅ Connected successfully!")
        
        print("2. Logging in...")
        server.login(username, password)
        print("   ✅ Login successful!")
        
        print("3. Preparing test email...")
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = "DARI Wallet - SMTP Test"
        
        body = """
        <html>
        <body>
            <h2>SMTP Configuration Test</h2>
            <p>If you received this email, your SMTP configuration is working correctly!</p>
            <p><strong>Configuration:</strong></p>
            <ul>
                <li>Host: {}</li>
                <li>Port: {}</li>
                <li>SSL: Enabled</li>
            </ul>
            <p>You can now use these settings on Render.</p>
        </body>
        </html>
        """.format(host, port)
        
        msg.attach(MIMEText(body, 'html'))
        
        print("4. Sending test email...")
        server.sendmail(from_email, to_email, msg.as_string())
        print("   ✅ Email sent successfully!")
        
        print("5. Closing connection...")
        server.quit()
        print("   ✅ Connection closed!")
        
        print(f"\n{'='*60}")
        print("✅ ALL TESTS PASSED!")
        print(f"{'='*60}")
        print(f"\nCheck your inbox at: {to_email}")
        print("If you received the email, copy these settings to Render:\n")
        print(f"SMTP_HOST={host}")
        print(f"SMTP_PORT={port}")
        print(f"SMTP_USE_SSL=true")
        print(f"SMTP_USERNAME={username}")
        print(f"SMTP_PASSWORD=your-password")
        print(f"FROM_EMAIL={from_email}")
        print(f"OTP_EMAIL_ENABLED=true")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ Authentication failed: {e}")
        print("\n💡 Solutions:")
        print("   - For Gmail: Use App Password (not regular password)")
        print("     Generate at: https://myaccount.google.com/apppasswords")
        print("   - For Zoho: Use your account password")
        print("   - Verify username and password are correct")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"   ❌ Connection failed: {e}")
        print("\n💡 Solutions:")
        print("   - Check if host and port are correct")
        print("   - Verify your internet connection")
        print("   - Try port 587 with TLS instead")
        return False
        
    except TimeoutError as e:
        print(f"   ❌ Connection timed out: {e}")
        print("\n💡 Solutions:")
        print("   - Check your firewall settings")
        print("   - Verify SMTP server is reachable")
        print("   - Try a different network")
        return False
        
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        print(f"\n💡 Error type: {type(e).__name__}")
        return False


def test_smtp_tls(host, port, username, password, from_email, to_email):
    """Test SMTP with TLS (port 587)"""
    print(f"\n{'='*60}")
    print(f"Testing SMTP_TLS: {host}:{port}")
    print(f"{'='*60}")
    
    try:
        print("1. Connecting to SMTP server...")
        server = smtplib.SMTP(host, port, timeout=30)
        print("   ✅ Connected successfully!")
        
        print("2. Starting TLS...")
        server.starttls()
        print("   ✅ TLS started!")
        
        print("3. Logging in...")
        server.login(username, password)
        print("   ✅ Login successful!")
        
        print("4. Preparing test email...")
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = "DARI Wallet - SMTP Test"
        
        body = """
        <html>
        <body>
            <h2>SMTP Configuration Test</h2>
            <p>If you received this email, your SMTP configuration is working correctly!</p>
            <p><strong>Configuration:</strong></p>
            <ul>
                <li>Host: {}</li>
                <li>Port: {}</li>
                <li>TLS: Enabled</li>
            </ul>
            <p>You can now use these settings on Render.</p>
        </body>
        </html>
        """.format(host, port)
        
        msg.attach(MIMEText(body, 'html'))
        
        print("5. Sending test email...")
        server.sendmail(from_email, to_email, msg.as_string())
        print("   ✅ Email sent successfully!")
        
        print("6. Closing connection...")
        server.quit()
        print("   ✅ Connection closed!")
        
        print(f"\n{'='*60}")
        print("✅ ALL TESTS PASSED!")
        print(f"{'='*60}")
        print(f"\nCheck your inbox at: {to_email}")
        print("If you received the email, copy these settings to Render:\n")
        print(f"SMTP_HOST={host}")
        print(f"SMTP_PORT={port}")
        print(f"SMTP_USE_TLS=true")
        print(f"SMTP_USERNAME={username}")
        print(f"SMTP_PASSWORD=your-password")
        print(f"FROM_EMAIL={from_email}")
        print(f"OTP_EMAIL_ENABLED=true")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ Authentication failed: {e}")
        print("\n💡 Solutions:")
        print("   - For Gmail: Use App Password (not regular password)")
        print("     Generate at: https://myaccount.google.com/apppasswords")
        print("   - Verify username and password are correct")
        return False
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print(f"\n💡 Error type: {type(e).__name__}")
        return False


def main():
    print("\n" + "="*60)
    print("DARI Wallet Backend - SMTP Configuration Test")
    print("="*60)
    
    # Get configuration from user
    print("\nEnter your SMTP configuration:")
    print("(Press Ctrl+C to cancel)\n")
    
    try:
        host = input("SMTP Host (e.g., smtp.gmail.com): ").strip()
        port = input("SMTP Port (465 for SSL, 587 for TLS): ").strip()
        username = input("SMTP Username (your email): ").strip()
        password = input("SMTP Password (app password): ").strip()
        from_email = input("From Email (same as username): ").strip() or username
        to_email = input("Test Email (where to send test): ").strip() or username
        
        port = int(port)
        
        # Test based on port
        if port == 465:
            test_smtp_ssl(host, port, username, password, from_email, to_email)
        elif port == 587:
            test_smtp_tls(host, port, username, password, from_email, to_email)
        else:
            print(f"\n⚠️  Unusual port: {port}")
            print("Common ports: 465 (SSL) or 587 (TLS)")
            choice = input("Try SSL (s) or TLS (t)? ").lower()
            if choice == 's':
                test_smtp_ssl(host, port, username, password, from_email, to_email)
            else:
                test_smtp_tls(host, port, username, password, from_email, to_email)
                
    except KeyboardInterrupt:
        print("\n\n❌ Test cancelled by user")
        sys.exit(0)
    except ValueError as e:
        print(f"\n❌ Invalid port number: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
