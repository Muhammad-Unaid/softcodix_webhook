import os
import json
import requests
import concurrent.futures
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.mail import send_mail
from .models import PageContent
import threading 

SERVICE_QUESTIONS = {
    "website": [
        "What type of website do you need? (Business / E-commerce / Portfolio / Blog )",
        "Approximately how many pages do you need?",
        "What is your budget range?"
    ],
    "mobile-app": [
        "Do you need Android, iOS, or both?",
        "What is the purpose of the app? (Business , E-commerce , Social , etc.)",
        "How many users are expected?",
        "Any special features needed? (Push notifications, payment, etc.)",
        "What is your budget range?"
    ],
    "marketing": [
        "What type of marketing services do you need? (Social , SEO, Paid Ads, Email , etc.)",
        "Which platforms would you like to focus on? (Facebook , Instagram , Google, TikTok, etc.)",
        "What is your approximate monthly marketing budget?",
        "Who is your target audience? (Age, location, interests, profession, etc.)",
        "Are there any ongoing marketing campaigns? If yes, could you share a brief overview?"
    ],
    "chatbot": [
        "Which platform do you need the chatbot for? (Website , WhatsApp , Facebook)",
        "What is the purpose of the chatbot? (Customer support, lead generation, AI Assistant)",
        "In which language should the chatbot reply? (English, Urdu, both)",
        "Do you need an AI-powered chatbot or a simple rule-based one?"
    ],
    "design": [
        "What type of design do you need? (Logo, Branding, Social Media Posts, UI/UX, Print)",
        "If you need a logo, what is the business name and is there a tagline?",
        "In which file format do you need the final design? (PNG, PSD, AI, PDF)",
        "What is your budget range?"
    ]
}

SERVICE_KEYWORDS = {
    "website": ["website", "web", "site", "webpage"],
    "mobile-app": ["app", "mobile", "application", "android", "ios", "apk"],
    "marketing": ["marketing", "ads", "seo", "social media", "facebook ads", "instagram ads"],
    "chatbot": ["chatbot", "bot", "chat bot", "whatsapp bot"],
    "design": ["design", "logo", "graphics", "branding", "ui", "ux"]
}

def send_lead_email_async(lead_data):
    """Send email in background thread"""
    thread = threading.Thread(target=send_lead_email, args=(lead_data,))
    thread.daemon = True  # Thread will die when main program exits
    thread.start()
    print("[Email] ✅ Email sending started in background")

# def send_lead_email(lead_data):
#     """Send lead details via email"""
#     try:
#         service = lead_data.get('service', 'N/A')
#         name = lead_data.get('name', 'N/A')
#         phone = lead_data.get('phone', 'N/A')
#         email = lead_data.get('email', 'N/A')
#         answers = lead_data.get('answers', {})
        
#         print(f"[Email] Preparing to send lead email...")
#         print(f"[Email] Service: {service}")
#         print(f"[Email] Name: {name}")
#         print(f"[Email] Phone: {phone}")
#         print(f"[Email] Email: {email}")
#         print(f"[Email] Answers: {answers}")
        
#         if not name or name == 'N/A':
#             print("[Email] ⚠️ WARNING: Name is empty!")
#         if not phone or phone == 'N/A':
#             print("[Email] ⚠️ WARNING: Phone is empty!")
#         if not email or email == 'N/A':
#             print("[Email] ⚠️ WARNING: Email is empty!")
        
#         company_email_body = f"""
# 🎉 New Lead from Chatbot!

# 📋 Service Interested: {service.upper()}

# 👤 Contact Details:
# - Name: {name}
# - Phone: {phone}
# - Email: {email}

# 💬 Responses:
# """
        
#         for question, answer in answers.items():
#             company_email_body += f"\nQ: {question}\nA: {answer}\n"
        
#         company_email_body += "\n---\nPlease contact this lead ASAP!"
        
#         user_email_body = f"""
# Hi {name},

# Thank you for your interest in our {service.replace('-', ' ').upper()} services! 🎉

# We have received your inquiry and our team will contact you within 24 hours.

# Your Details:
# - Service: {service.upper()}
# - Phone: {phone}
# - Email: {email}

# If you have any urgent questions, feel free to call us at 02138899998 or WhatsApp at 03218795135.

# Best Regards,
# Softcodix Team
# """
        
#         print(f"[Email] Sending to company: {settings.LEAD_EMAIL}")
#         print(f"[Email] Sending to user: {email}")
        
#         send_mail(
#             subject=f'New {service.upper()} Lead - {name}',
#             message=company_email_body,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             recipient_list=[settings.LEAD_EMAIL],
#             fail_silently=False,
#         )
        
#         send_mail(
#             subject=f'Thank You for Contacting Softcodix - {service.upper()}',
#             message=user_email_body,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             recipient_list=[email],
#             fail_silently=False,
#         )
        
#         print(f"[Email] ✅ Both emails sent successfully!")
#         return True
        
#     except Exception as e:
#         print(f"[Email] ❌ Error: {str(e)}")
#         return False

def send_lead_email(lead_data):
    """Send lead details via email with HTML card design"""
    try:
        from django.core.mail import EmailMultiAlternatives
        
        service = lead_data.get('service', 'N/A')
        name = lead_data.get('name', 'N/A')
        phone = lead_data.get('phone', 'N/A')
        email = lead_data.get('email', 'N/A')
        answers = lead_data.get('answers', {})
        
        print(f"[Email] Preparing to send lead email...")
        print(f"[Email] Service: {service}")
        print(f"[Email] Name: {name}")
        print(f"[Email] Phone: {phone}")
        print(f"[Email] Email: {email}")
        print(f"[Email] Full lead_data: {lead_data}")
        
        # ✅ Better validation
        if not name or name == 'N/A' or name.strip() == '':
            print("[Email] ⚠️ WARNING: Name is empty!")
            name = "Guest User"
        if not phone or phone == 'N/A' or phone.strip() == '':
            print("[Email] ⚠️ WARNING: Phone is empty!")
            phone = "Not provided"
        if not email or email == 'N/A' or '@' not in email:
            print("[Email] ⚠️ ERROR: Invalid email!")
            return False
        
        # ✅ Build Q&A HTML
        qa_html = ""
        for question, answer in answers.items():
            qa_html += f"""
            <div style="margin-bottom: 15px; padding: 12px; background: #f8f9fa; border-left: 4px solid #E31E24; border-radius: 4px;">
                <p style="margin: 0 0 8px 0; font-weight: 600; color: #1B2A4A;">❓ {question}</p>
                <p style="margin: 0; color: #333;">✅ {answer}</p>
            </div>
            """
        
        # ✅ Company Email HTML
        company_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 20px; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f0f2f5;">
            <div style="max-width: 650px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 16px rgba(0,0,0,0.12);">
                
                <div style="background: linear-gradient(135deg, #1B2A4A 0%, #0D1625 100%); padding: 40px 20px; text-align: center;">
                    <div style="background: white; display: inline-block; padding: 15px 30px; border-radius: 8px;">
                        <img src="data:image/png;base64,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" alt="Softcodix" style="width: 280px; height: auto; display: block;">
                    </div>
                    <h1 style="color: white; margin: 20px 0 0 0; font-size: 28px;">🎉 New Lead Alert!</h1>
                </div>
                
               
                
                <div style="background: linear-gradient(90deg, #E31E24 0%, #C71920 100%); padding: 18px; text-align: center;">
                    <p style="margin: 0; font-size: 20px; font-weight: bold; color: white;">
                        📋 SERVICE: {service.upper().replace('-', ' ')}
                    </p>
                </div>
                
                <div style="padding: 35px 30px;">
                    <h2 style="color: #1B2A4A; border-bottom: 3px solid #E31E24; padding-bottom: 12px;">
                        👤 Contact Information
                    </h2>
                    
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px; border: 2px solid #1B2A4A;">
                        <tr>
                            <td style="padding: 15px; background: #1B2A4A; color: white; font-weight: 700; width: 40%;">Name:</td>
                            <td style="padding: 15px; background: white; border-left: 2px solid #1B2A4A;">{name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 15px; background: #1B2A4A; color: white; font-weight: 700; border-top: 2px solid white;">Phone:</td>
                            <td style="padding: 15px; background: white; border-left: 2px solid #1B2A4A; border-top: 2px solid #e0e0e0;">{phone}</td>
                        </tr>
                        <tr>
                            <td style="padding: 15px; background: #1B2A4A; color: white; font-weight: 700; border-top: 2px solid white;">Email:</td>
                            <td style="padding: 15px; background: white; border-left: 2px solid #1B2A4A; border-top: 2px solid #e0e0e0;">{email}</td>
                        </tr>
                    </table>
                    
                    <h2 style="color: #1B2A4A; border-bottom: 3px solid #E31E24; padding-bottom: 12px;">
                        💬 Requirements
                    </h2>
                    
                    {qa_html}
                    
                </div>
                
                <div style="background: linear-gradient(135deg, #1B2A4A 0%, #0D1625 100%); color: white; padding: 25px; text-align: center;">
                    <p style="margin: 0 0 12px 0; font-weight: bold; font-size: 18px; color: #E31E24;">⚡ Contact ASAP!</p>
                    <p style="margin: 0; font-size: 15px;">Contact within 24 hours for best conversion 🚀</p>
                </div>
                
            </div>
        </body>
        </html>
        """
        
        # ✅ User Email HTML
        user_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 20px; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f0f2f5;">
            <div style="max-width: 650px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 16px rgba(0,0,0,0.12);">
                
                <div style="background: linear-gradient(135deg, #1B2A4A 0%, #0D1625 100%); padding: 40px 20px; text-align: center;">
                    <div style="background: white; display: inline-block; padding: 15px 30px; border-radius: 8px;">
                        <img src="data:image/png;base64,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" alt="Softcodix" style="width: 280px; height: auto; display: block;">
                    </div>
                    <h1 style="color: white; margin: 20px 0 0 0; font-size: 28px;">Thank You! 🎉</h1>
                </div>
                
                <div style="padding: 35px 30px;">
                    <p style="font-size: 18px; color: #1B2A4A; font-weight: 600;">
                        Hi <span style="color: #E31E24;">{name}</span>,
                    </p>
                    
                    <p style="font-size: 16px; color: #333; line-height: 1.8;">
                        Thank you for your interest in our <strong style="color: #1B2A4A;">{service.upper().replace('-', ' ')}</strong> services! 🚀
                    </p>
                    
                    <div style="background: linear-gradient(135deg, #E31E24 0%, #C71920 100%); border-radius: 8px; padding: 20px; margin: 25px 0; text-align: center;">
                        <p style="margin: 0; color: white; font-weight: 700; font-size: 18px;">✅ Inquiry Received!</p>
                    </div>
                    
                    <p style="font-size: 16px; color: #333; line-height: 1.8;">
                        Our team will contact you within <strong style="color: #E31E24;">24 hours</strong>.
                    </p>
                    
                    <h3 style="color: #1B2A4A; margin-top: 30px; border-bottom: 2px solid #E31E24; padding-bottom: 10px;">📞 Need Help?</h3>
                    
                    <table style="width: 100%; margin: 20px 0;">
                        <tr>
                            <td style="padding: 15px; background: #1B2A4A; border-radius: 8px; text-align: center;">
                                <strong style="color: white;">📞 Call: 02138899998</strong>
                            </td>
                        </tr>
                        <tr><td style="height: 12px;"></td></tr>
                        <tr>
                            <td style="padding: 15px; background: #25D366; border-radius: 8px; text-align: center;">
                                <a href="https://wa.me/923218795135" style="color: white; text-decoration: none; font-weight: bold;">
                                    💬 WhatsApp: +92 321 8795135
                                </a>
                            </td>
                        </tr>
                    </table>
                    
                </div>
                
                <div style="background: linear-gradient(135deg, #1B2A4A 0%, #0D1625 100%); color: white; padding: 25px; text-align: center;">
                    <p style="margin: 0; font-weight: bold; color: #E31E24;">SOFTCODIX</p>
                    <p style="margin: 8px 0 0 0; font-size: 14px;">Simplified Digital Solution 🚀</p>
                </div>
                
            </div>
        </body>
        </html>
        """
        
        # ✅ Send Company Email
        print(f"[Email] Sending company email to: {settings.LEAD_EMAIL}")
        company_msg = EmailMultiAlternatives(
            subject=f'🎯 New {service.upper()} Lead - {name}',
            body=f"New lead from {name}. Check HTML version.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.LEAD_EMAIL]
        )
        company_msg.attach_alternative(company_html, "text/html")
        company_msg.send()
        print("[Email] ✅ Company email sent!")
        
        # ✅ Send User Email
        print(f"[Email] Sending user email to: {email}")
        user_msg = EmailMultiAlternatives(
            subject=f'✅ Thank You - Softcodix {service.upper()}',
            body=f"Hi {name}, Thank you!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email]
        )
        user_msg.attach_alternative(user_html, "text/html")
        user_msg.send()
        print("[Email] ✅ User email sent!")
        
        print(f"[Email] ✅ Both emails sent!")
        return True
        
    except Exception as e:
        print(f"[Email] ❌ Error: {str(e)}")
        import traceback
        print(f"[Email] Traceback: {traceback.format_exc()}")
        return False
    
    
def get_active_service_context(output_contexts):
    """Extract active service context and its parameters"""
    for context in output_contexts:
        context_name = context.get("name", "")
        for service in ["website", "mobile-app", "marketing", "chatbot", "design"]:
            if f"{service}-context" in context_name:
                params = context.get("parameters", {})
                print(f"[Context] Found active: {service}-context")
                print(f"[Context] Parameters: {params}")
                return service, params
    return None, {}


def has_any_active_service_context(output_contexts):
    """Check if ANY service context is active"""
    for context in output_contexts:
        context_name = context.get("name", "")
        for service in ["website", "mobile-app", "marketing", "chatbot", "design"]:
            if f"{service}-context" in context_name:
                lifespan = context.get("lifespanCount", 0)
                if lifespan > 0:
                    return True
    return False


def detect_service_from_query(query):
    """Detect service intent from user query using keywords"""
    query_lower = query.lower()
    
    for service, keywords in SERVICE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_lower:
                print(f"[Keyword Detection] Found '{keyword}' -> Service: {service}")
                return service
    
    return None


def query_gemini_softcodix(user_query, website_content, services, timeout=4):
    """Ask Gemini to answer user query based on Softcodix website data"""
    try:
        prompt = f"""
        You are a helpful assistant for **Softcodix**.
        You are a friendly **sales agent** for Softcodix.

        📝 RULES:
        - Always reply in same language as user query.
        - If language is "urdu", reply in **Roman Urdu** (English alphabets only).
        - If language is "English", reply in **English**.
        - Keep answers short (3-5 lines).
        - Be professional but friendly, like chatting on WhatsApp.
        - Do NOT always start with greetings.
        - If query is about services, explain briefly with 2-3 bullet points.
        - End with a small call-to-action.

        Company Info:
        {website_content}

        Our Services:
        {services}  

        User asked: {user_query}
        """

        GEMINI_API_KEY = getattr(settings, "GEMINI_API_KEY", None)
        if not GEMINI_API_KEY:
            return "⚠️ Gemini API key not configured."

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            return f"⚠️ Gemini error: {response.status_code}"

    except Exception as e:
        return f"⚠️ Gemini exception: {str(e)}"


def query_with_timeout_softcodix(user_query, website_content, services, timeout=4):
    """Run Gemini query but fallback if slow"""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(query_gemini_softcodix, user_query, website_content, services, timeout)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return "⏳ Server busy hai, please try again shortly."


def smart_query_handler_softcodix(user_query):
    """Main Softcodix chatbot handler"""
    db_result = PageContent.objects.filter(content__icontains=user_query)
    if db_result.exists():
        snippet = db_result.first().content[:400]
        return f"🔍 I found this info:\n{snippet}"

    website_content = "Softcodix is an IT solutions company providing AI, automation, and custom development."
    services = "- AI Chatbots\n- Web & Mobile Development\n- Business Automation\n- Cloud & API Integrations"

    return query_with_timeout_softcodix(user_query, website_content, services, timeout=4)


@csrf_exempt
def dialogflow_webhook(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    body = json.loads(request.body.decode("utf-8"))
    user_query = body.get("queryResult", {}).get("queryText", "")
    intent_name = body.get("queryResult", {}).get("intent", {}).get("displayName", "")
    parameters = body.get("queryResult", {}).get("parameters", {})
    output_contexts = body.get("queryResult", {}).get("outputContexts", [])
    session = body.get("session", "")

    print(f"\n{'='*60}")
    print(f"[Webhook] User Query: {user_query}")
    print(f"[Webhook] Intent: {intent_name}")
    print(f"[Webhook] Parameters: {parameters}")
    print(f"[Webhook] Active Contexts: {[c.get('name', '').split('/')[-1] for c in output_contexts]}")
    print(f"{'='*60}\n")

    # Block service-inquiry intents if another service context is already active
    if intent_name in ["website-inquiry", "mobile-app-inquiry", "marketing-inquiry", "chatbot-inquiry", "design-inquiry"]:
        requested_service = intent_name.replace("-inquiry", "")
        active_service, _ = get_active_service_context(output_contexts)
        
        if active_service and active_service != requested_service:
            print(f"[BLOCKED] {intent_name} ignored because {active_service}-context is active")
            print(f"[BLOCKED] Treating as answer to {active_service} question")
            intent_name = "Default Fallback Intent"
        else:
            service = requested_service
            first_question = SERVICE_QUESTIONS[service][0]
            
            print(f"[Service Selected] {service}")
            print(f"[First Question] {first_question}")
            
            return JsonResponse({
                "fulfillmentText": f"Great! Aap {service.replace('-', ' ').upper()} development mein interested hain. ✨\n\nMain kuch quick questions puchna chahta hoon taake hum aapki requirements achhe se samajh sakein.\n\n{first_question}",
                "outputContexts": [
                    {
                        "name": f"{session}/contexts/{service}-context",
                        "lifespanCount": 20,
                        "parameters": {
                            "service": service,
                            "question_index": 1,
                            "answers": {}
                        }
                    }
                ]
            })
    
    # Service Questions Intent
    if intent_name == "service-questions":
        print("[service-questions intent triggered]")
        
        active_service, context_params = get_active_service_context(output_contexts)
        
        if not active_service:
            print("[ERROR] No active service context found")
            return JsonResponse({
                "fulfillmentText": "⚠️ Session expired. Please select service again."
            })
        
        service = context_params.get("service", active_service)
        question_index = int(float(context_params.get("question_index", 0)))
        answers = context_params.get("answers", {})
        
        print(f"[Question Flow] Service: {service}, Index: {question_index}")
        
        if question_index > 0 and question_index <= len(SERVICE_QUESTIONS[service]):
            prev_question = SERVICE_QUESTIONS[service][question_index - 1]
            answers[prev_question] = user_query
            print(f"[Answer Stored] {prev_question} = {user_query}")
        
        if question_index < len(SERVICE_QUESTIONS[service]):
            next_question = SERVICE_QUESTIONS[service][question_index]
            print(f"[Next Question] {next_question}")
            
            return JsonResponse({
                "fulfillmentText": next_question,
                "outputContexts": [
                    {
                        "name": f"{session}/contexts/{service}-context",
                        "lifespanCount": 20,
                        "parameters": {
                            "service": service,
                            "question_index": question_index + 1,
                            "answers": answers
                        }
                    }
                ]
            })
        else:
            print("[Questions Complete] Moving to contact collection")
            
            return JsonResponse({
                "fulfillmentText": "Perfect! 🎯\n\nAb main aapki contact details collect karta hoon taake humari team aapse contact kar sake.\n\nAapka naam kya hai?",
                "outputContexts": [
                    {
                        "name": f"{session}/contexts/collect-details",
                        "lifespanCount": 10,
                        "parameters": {
                            "service": service,
                            "answers": answers,
                            "step": "name"
                        }
                    }
                ]
            })

    # Collect Contact Details
    elif intent_name == "collect-contact-details":
        collect_context = None
        for context in output_contexts:
            if "collect-details" in context.get("name", ""):
                collect_context = context
                break
        
        if not collect_context:
            print("[Contact] ❌ No collect-details context found")
            return JsonResponse({
                "fulfillmentText": "⚠️ Session expired. Please start again."
            })
        
        context_params = collect_context.get("parameters", {})
        step = context_params.get("step")
        service = context_params.get("service")
        answers = context_params.get("answers", {})
        
        print(f"[Contact] Step: {step}")
        print(f"[Contact] Service: {service}")
        
        if step == "name":
            name = parameters.get("person", {}).get("name") if isinstance(parameters.get("person"), dict) else parameters.get("person")
            if not name:
                name = user_query.strip()
            
            print(f"[Contact] Name collected: {name}")
            
            return JsonResponse({
                "fulfillmentText": f"Thanks {name}! 😊\n\nAapka phone number kya hai?",
                "outputContexts": [
                    {
                        "name": f"{session}/contexts/collect-details",
                        "lifespanCount": 10,
                        "parameters": {
                            "service": service,
                            "answers": answers,
                            "name": name,
                            "step": "phone"
                        }
                    }
                ]
            })
        
        elif step == "phone":
            phone = parameters.get("phone-number")
            if not phone:
                phone = user_query.strip()
            
            print(f"[Contact] Phone collected: {phone}")
            
            return JsonResponse({
                "fulfillmentText": "Great! 📱\n\nAur aapka email address?",
                "outputContexts": [
                    {
                        "name": f"{session}/contexts/collect-details",
                        "lifespanCount": 10,
                        "parameters": {
                            "service": service,
                            "answers": answers,
                            "name": context_params.get("name"),
                            "phone": phone,
                            "step": "email"
                        }
                    }
                ]
            })
        
        elif step == "email":
            email = user_query.strip()
            # email = parameters.get("email")
            # if not email:
            #     email = user_query.strip()
            
            print(f"[Contact] Email collected: {email}")
            
            lead_name = context_params.get("name", "Not provided")
            lead_phone = context_params.get("phone", "Not provided")

            print(f"[Lead Data] Name: {lead_name}")
            print(f"[Lead Data] Phone: {lead_phone}")
            print(f"[Lead Data] Email: {email}")
            print(f"[Lead Data via Fallback] Full context_params: {context_params}")  # ✅ ADD THIS

            lead_data = {
                "service": service,
                "name": lead_name,
                "phone": lead_phone,
                "email": email,
                "answers": answers
            }
            
            print(f"[Lead Data] Complete lead: {lead_data}")
            
            # email_sent = send_lead_email(lead_data)
            
            # if email_sent:
            #     return JsonResponse({
            #         "fulfillmentText": f"Perfect! ✅\n\nThank you {lead_name}! Aapki details successfully submit ho gayi hain.\n\nHumari team 24 hours ke andar aapse contact karegi. 🚀\n\nKya main aur kuch help kar sakta hoon?"
            #     })
            # else:
            #     return JsonResponse({
            #         "fulfillmentText": "⚠️ Sorry, kuch technical issue hai. Please try again or call us at 02138899998"
            #     })
            send_lead_email_async(lead_data)

            return JsonResponse({
                "fulfillmentText": f"Perfect! ✅\n\nThank you {lead_name}! Aapki details successfully submit ho gayi hain.\n\nHumari team 24 hours ke andar aapse contact karegi. 🚀\n\nKya main aur kuch help kar sakta hoon?"
            })
            
    # Helpline Intent
    elif intent_name == "helpline":
        return JsonResponse({
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [
                            "📞 Our helpline number is: 02138899998\nFeel free to call us anytime during business hours. We're here to help! 😊"
                        ]
                    }
                },
                {
                    "payload": {
                        "richContent": [
                            [
                                {
                                    "icon": {
                                        "type": "chevron_right",
                                        "color": "#25D366"
                                    },
                                    "text": "📱 WhatsApp",
                                    "type": "button",
                                    "link": "https://wa.me/923151179953"
                                }
                            ]
                        ]
                    }
                }
            ]
        })

    # LLM Query Intent
    elif intent_name == "LLMQueryIntent":
        reply = smart_query_handler_softcodix(user_query)
        return JsonResponse({"fulfillmentText": reply})

    # Default Fallback Intent
    elif intent_name == "Default Fallback Intent":
        print("[Fallback] Checking for active contexts...")
        
        active_service, context_params = get_active_service_context(output_contexts)
        
        if active_service:
            print(f"[Fallback] User is in {active_service} question flow")
            
            service = context_params.get("service", active_service)
            question_index = int(float(context_params.get("question_index", 0)))
            answers = context_params.get("answers", {})
            
            print(f"[Question Flow] Current index: {question_index}")
            print(f"[Question Flow] Total questions: {len(SERVICE_QUESTIONS[service])}")
            
            if question_index > 0 and question_index <= len(SERVICE_QUESTIONS[service]):
                prev_question = SERVICE_QUESTIONS[service][question_index - 1]
                answers[prev_question] = user_query
                print(f"[Answer Stored] Q{question_index}: {user_query}")
            
            if question_index < len(SERVICE_QUESTIONS[service]):
                next_question = SERVICE_QUESTIONS[service][question_index]
                print(f"[Next Question] {next_question}")
                
                return JsonResponse({
                    "fulfillmentText": next_question,
                    "outputContexts": [
                        {
                            "name": f"{session}/contexts/{service}-context",
                            "lifespanCount": 20,
                            "parameters": {
                                "service": service,
                                "question_index": question_index + 1,
                                "answers": answers
                            }
                        }
                    ]
                })
            else:
                print("[Questions Complete] Moving to contact collection")
                
                return JsonResponse({
                    "fulfillmentText": "Perfect! 🎯\n\nAb main aapki contact details collect karta hoon taake humari team aapse contact kar sake.\n\nAapka naam kya hai?",
                    "outputContexts": [
                        {
                            "name": f"{session}/contexts/collect-details",
                            "lifespanCount": 10,
                            "parameters": {
                                "service": service,
                                "answers": answers,
                                "step": "name"
                            }
                        }
                    ]
                })
        
        # Check if in contact collection flow
        collect_context = None
        for context in output_contexts:
            if "collect-details" in context.get("name", ""):
                collect_context = context
                break
        
        if collect_context:
            print("[Fallback] User is in contact collection flow")
            
            context_params = collect_context.get("parameters", {})
            step = context_params.get("step")
            service = context_params.get("service")
            answers = context_params.get("answers", {})
            
            if not step:
                print("[Fallback] ⚠️ No step found in collect-details context")
                return JsonResponse({
                    "fulfillmentText": "⚠️ Session expired. Please start again."
                })
            
            if step == "name":
                name = user_query.strip()
                print(f"[Contact via Fallback] Name: {name}")
                
                return JsonResponse({
                    "fulfillmentText": f"Thanks {name}! 😊\n\nAapka phone number kya hai?",
                    "outputContexts": [
                        {
                            "name": f"{session}/contexts/collect-details",
                            "lifespanCount": 10,
                            "parameters": {
                                "service": service,
                                "answers": answers,
                                "name": name,
                                "step": "phone"
                            }
                        }
                    ]
                })
            
            elif step == "phone":
                phone = user_query.strip()
                print(f"[Contact via Fallback] Phone: {phone}")
                
                return JsonResponse({
                    "fulfillmentText": "Great! 📱\n\nAur aapka email address?",
                    "outputContexts": [
                        {
                            "name": f"{session}/contexts/collect-details",
                            "lifespanCount": 10,
                            "parameters": {
                                "service": service,
                                "answers": answers,
                                "name": context_params.get("name"),
                                "phone": phone,
                                "step": "email"
                            }
                        }
                    ]
                })
            
            elif step == "email":
                email = user_query.strip()
                print(f"[Contact via Fallback] Email: {email}")

                lead_name = context_params.get("name", "Not provided")
                lead_phone = context_params.get("phone", "Not provided")

                print(f"[Lead Data via Fallback] Name: {lead_name}")
                print(f"[Lead Data via Fallback] Phone: {lead_phone}")
                print(f"[Lead Data via Fallback] Email: {email}")

                lead_data = {
                    "service": service,
                    "name": lead_name,
                    "phone": lead_phone,
                    "email": email,
                    "answers": answers
                }
                
                print(f"[Lead Data] {lead_data}")
                
                email_sent = send_lead_email(lead_data)
                
                if email_sent:
                    return JsonResponse({
                        "fulfillmentText": f"Perfect! ✅\n\nThank you {lead_name}! Aapki details successfully submit ho gayi hain.\n\nHumari team 24 hours ke andar aapse contact karegi. 🚀\n\nKya main aur kuch help kar sakta hoon?"
                    })
                else:
                    return JsonResponse({
                        "fulfillmentText": "⚠️ Sorry, kuch technical issue hai. Please try again or call us at 02138899998"
                    })
        
        # Keyword detection only if no service context active
        if not has_any_active_service_context(output_contexts):
            detected_service = detect_service_from_query(user_query)
            
            if detected_service:
                print(f"[Fallback] Detected service from keywords: {detected_service}")
                first_question = SERVICE_QUESTIONS[detected_service][0]
                
                return JsonResponse({
                    "fulfillmentText": f"Great! Aap {detected_service.replace('-', ' ').upper()} development mein interested hain. ✨\n\nMain kuch quick questions puchna chahta hoon taake hum aapki requirements achhe se samajh sakein.\n\n{first_question}",
                    "outputContexts": [
                        {
                            "name": f"{session}/contexts/{detected_service}-context",
                            "lifespanCount": 20,
                            "parameters": {
                                "service": detected_service,
                                "question_index": 1,
                                "answers": {}
                            }
                        }
                    ]
                })
        else:
            print("[Fallback] Service context active - skipping keyword detection")
        
        # No context - use Gemini
        print("[Fallback] No active context, using Gemini")
        reply = smart_query_handler_softcodix(user_query)
        return JsonResponse({"fulfillmentText": reply})

    # Unknown Intent
    else:
        print(f"[Unknown Intent] {intent_name}")
        reply = smart_query_handler_softcodix(user_query)
        return JsonResponse({"fulfillmentText": reply})