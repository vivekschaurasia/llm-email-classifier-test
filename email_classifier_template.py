# Configuration and imports
import os
import json
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Sample email dataset
sample_emails = [
    {
        "id": "001",
        "from": "angry.customer@example.com",
        "subject": "Broken product received",
        "body": "I received my order #12345 yesterday but it arrived completely damaged. This is unacceptable and I demand a refund immediately. This is the worst customer service I've experienced.",
        "timestamp": "2024-03-15T10:30:00Z"
    },
    {
        "id": "002",
        "from": "curious.shopper@example.com",
        "subject": "Question about product specifications",
        "body": "Hi, I'm interested in buying your premium package but I couldn't find information about whether it's compatible with Mac OS. Could you please clarify this? Thanks!",
        "timestamp": "2024-03-15T11:45:00Z"
    },
    {
        "id": "003",
        "from": "happy.user@example.com",
        "subject": "Amazing customer support",
        "body": "I just wanted to say thank you for the excellent support I received from Sarah on your team. She went above and beyond to help resolve my issue. Keep up the great work!",
        "timestamp": "2024-03-15T13:15:00Z"
    },
    {
        "id": "004",
        "from": "tech.user@example.com",
        "subject": "Need help with installation",
        "body": "I've been trying to install the software for the past hour but keep getting error code 5123. I've already tried restarting my computer and clearing the cache. Please help!",
        "timestamp": "2024-03-15T14:20:00Z"
    },
    {
        "id": "005",
        "from": "business.client@example.com",
        "subject": "Partnership opportunity",
        "body": "Our company is interested in exploring potential partnership opportunities with your organization. Would it be possible to schedule a call next week to discuss this further?",
        "timestamp": "2024-03-15T15:00:00Z"
    }
]


class EmailProcessor:
    def __init__(self):
        """Initialize the email processor with OpenAI API key."""
        self.client = OpenAI(api_key= "OPENAI_API_KEY")

        # Define valid categories
        self.valid_categories = {
            "complaint", "inquiry", "feedback",
            "support_request", "other"
        }

    def classify_email(self, email: Dict) -> Optional[str]:
        """
        Classify an email using LLM.
        Returns the classification category or None if classification fails.
        
        TODO: 
        1. Design and implement the classification prompt
        2. Make the API call with appropriate error handling
        3. Validate and return the classification
        """
        try:
            #Part 3
            #Few shot learning
            prompt = ("Classify this email into one of the following categories: "
            "complaint, inquiry, feedback,support_request, other."
            "Focus on the primary intent of the email. If the email is not complaint, inquiry, feedback,support_request then classify it as other"
            "Below are the few example: \n"
            " - Subject: \"Intrested in partnership\" , Body: \"Hey I am intrested in partnership. SO  lets do it.\" --> other\n"
            " - Subject: \"Need help in login\" , Body: \"I need your help in login into my account.\" --> support_request\n\n"
            f"Subject: {email["subject"]}\n"
            f"Body: {email["body"]}"
            
            )
            
            #Call Chatgpt API
            response = self.client.chat.completions.create(
                model= "gpt-3.5-turbo", #Model name
                messages= [{"role": "user" , "content": prompt}] ,
                temperature= 0.3, #not get too much randomness
                max_tokens= 10, #Number of max token GPT will produce
            )

            #using the response to get out classification
            classification = response.choices[0].message.content.strip().lower()

            if classification in self.valid_categories:
                logger.info(f"Email {email["id"]} is caassified as {classification}")
                return classification
            else:
                logger.warning("No category was found")
                return None
        except Exception as e:
            logger.error("GPT did not classify the Email")
            return None
        

    def generate_response(self, email: Dict, classification: str) -> Optional[str]:
        """
        Generate an automated response based on email classification.
        
        TODO:
        1. Design the response generation prompt
        2. Implement appropriate response templates
        3. Add error handling
        """
        try:
            

            every_category = {"complaint" : "Write a polite mail for a customer complaint.",
                             "inquiry" : "write a polite mail for a customer inquiry. ", 
                             "feedback" : "write a polite mail for a feedback.",
                             "support_request" : "write a polite mail for a customer support request.", 
                             "other": "Write a generic response for uncategorized emails."}
            prompt = (f"{every_category[classification]}\n"
                      f"Subject : {email["subject"]}\n"
                      f"Body : {email["body"]}"
            )

            #Call Chatgpt API for getting the response
            response = self.client.chat.completions.create(
                model= "gpt-3.5-turbo", #Model name
                messages= [{"role": "user" , "content": prompt}] ,
                temperature= 0.4, #not get too much randomness
                max_tokens= 100, #Number of max token GPT will produce
            )

            generated_response = response.choices[0].message.content.strip()
            logger.info(f"Email {email["id"]} is responded by GPT and the response is {generated_response}")


            return generated_response

        except Exception as e:
            logger.error("GPT did not respond to the Email")
            return None



class EmailAutomationSystem:
    def __init__(self, processor: EmailProcessor):
        """Initialize the automation system with an EmailProcessor."""
        self.processor = processor
        self.response_handlers = {
            "complaint": self._handle_complaint,
            "inquiry": self._handle_inquiry,
            "feedback": self._handle_feedback,
            "support_request": self._handle_support_request,
            "other": self._handle_other
        }

    def process_email(self, email: Dict) -> Dict:

        """
        Process a single email through the complete pipeline.
        Returns a dictionary with the processing results.
        
        TODO:
        1. Implement the complete processing pipeline
        2. Add appropriate error handling
        3. Return processing results
        """
        
        try:
            result = {"email_id" : None, "success": False, "classification": None, "response_sent" : False}
            #To get the id of an Email
            email_id = email["id"]

            if email_id is None:
                raise ValueError(f"Email id Not Found")
            
            #To get the classification of a specific email
            classification = self.processor.classify_email(email)
            if classification is None:
                raise ValueError(f"The GPT model did not classify the specific email")
            
            #Generate Response usong the GPT;s API
            response =  self.processor.generate_response(email, classification)
            
            if response is None:
                raise ValueError(f"The GPT model did not response the specific email")
            
            # Handle the response based on the classification

            handler = self.response_handlers.get(classification)
            if handler:
                handler(email, response)
                result["response_sent"] = True
            else:
                raise ValueError(f"No handler was found")
            
            result["email_id"] = email_id
            result["classification"] = classification
            result["success"] = True


        except Exception as e:
            logger.error(f"Email {email_id} did not processes properly")

        return result

    def _handle_complaint(self, email: Dict , response: str):
        """
        Handle complaint emails.
        TODO: Implement complaint handling logic
        """
        send_complaint_response(email["id"] , response)
        create_urgent_ticket(email["id"] , "complaint" , f"Subject: {email["subject"]}")

    def _handle_inquiry(self, email: Dict, response: str):
        """
        Handle inquiry emails.
        TODO: Implement inquiry handling logic
        """
        send_standard_response(email["id"], response)

    def _handle_feedback(self, email: Dict,  response: str):
        """
        Handle feedback emails.
        TODO: Implement feedback handling logic
        """
        send_standard_response(email["id"], response)

    def _handle_support_request(self, email: Dict, response: str):
        """
        Handle support request emails.
        TODO: Implement support request handling logic
        """
        send_standard_response(email["id"], response)
        create_support_ticket(email["id"], f"Subject: {email["subject"]}")


    def _handle_other(self, email: Dict, response: str):
        """
        Handle other category emails.
        TODO: Implement handling logic for other categories
        """
        send_standard_response(email["id"], response)

# Mock service functions
def send_complaint_response(email_id: str, response: str):
    """Mock function to simulate sending a response to a complaint"""
    logger.info(f"Sending complaint response for email {email_id}")
    # In real implementation: integrate with email service


def send_standard_response(email_id: str, response: str):
    """Mock function to simulate sending a standard response"""
    logger.info(f"Sending standard response for email {email_id}")
    # In real implementation: integrate with email service


def create_urgent_ticket(email_id: str, category: str, context: str):
    """Mock function to simulate creating an urgent ticket"""
    logger.info(f"Creating urgent ticket for email {email_id}")
    # In real implementation: integrate with ticket system


def create_support_ticket(email_id: str, context: str):
    """Mock function to simulate creating a support ticket"""
    logger.info(f"Creating support ticket for email {email_id}")
    # In real implementation: integrate with ticket system


def log_customer_feedback(email_id: str, feedback: str):
    """Mock function to simulate logging customer feedback"""
    logger.info(f"Logging feedback for email {email_id}")
    # In real implementation: integrate with feedback system


def run_demonstration():
    """Run a demonstration of the complete system."""
    # Initialize the system
    processor = EmailProcessor()
    automation_system = EmailAutomationSystem(processor)

    # Process all sample emails
    results = []
    for email in sample_emails:
        logger.info(f"\nProcessing email {email['id']}...")
        result = automation_system.process_email(email)
        results.append(result)

    # Create a summary DataFrame
    df = pd.DataFrame(results)
    print("\nProcessing Summary:")
    print(df[["email_id", "success", "classification", "response_sent"]])

    return df


# Example usage:
if __name__ == "__main__":
    results_df = run_demonstration()
