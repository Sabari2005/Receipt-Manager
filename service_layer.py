import re
from datetime import date, datetime
from typing import List, Dict, Optional, Tuple, Union
import logging
import statistics
from pathlib import Path
from io import BytesIO
import numpy as np
import easyocr
from pdf2image import convert_from_bytes
from PIL import Image
import pandas as pd
import PyPDF2
from models import VendorBase, BillEntryBase, CategoryEnum
from db_handler import DatabaseHandler
from pydantic import ValidationError
import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnableSequence
from dateutil import parser

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReceiptProcessor:
    def __init__(self):
        self.db_handler = DatabaseHandler()
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.vendor_keywords = {
            CategoryEnum.FOOD: [
                # Restaurant types
                "restaurant", "cafe", "diner", "bistro", "eatery", "pizzeria", "steakhouse", 
                "trattoria", "brasserie", "taverna", "gastropub", "food truck", "food stall",
                # Food service
                "bakery", "patisserie", "confectionery", "delicatessen", "chocolatier",
                # Meal types
                "breakfast", "brunch", "lunch", "dinner", "supper", "takeaway", "delivery",
                # Cuisines
                "italian", "mexican", "chinese", "indian", "thai", "japanese", "mediterranean",
                "vegetarian", "vegan", "halal", "kosher", "gluten-free",
                # Food brands
                "mcdonald", "kfc", "burger king", "subway", "domino", "pizza hut",
                # Food delivery
                "zomato", "swiggy", "ubereats", "doordash", "grubhub", "deliveroo",
                # Misc
                "coffee", "tea house", "juice bar", "smoothie", "ice cream", "gelato",
                "donut", "bagel", "sandwich", "burger", "taco", "sushi", "ramen"
            ],
            
            CategoryEnum.TRANSPORT: [
                # Ride services
                "taxi", "uber", "lyft", "cab", "ride", "ola", "bolt",
                # Public transport
                "bus", "train", "metro", "subway", "tram", "ferry", "shuttle",
                # Vehicle related
                "fuel", "petrol", "diesel", "gas station", "charging station", "ev charge",
                "car wash", "auto repair", "tyre", "tire", "mechanic",
                # Parking/tolls
                "parking", "toll", "fastag", "valet",
                # Travel
                "airport", "airline", "flight", "railway", "transit", "commute"
            ],
            
            CategoryEnum.UTILITIES: [
                # Core utilities
                "electric", "water", "gas", "sewer", "waste", "recycling",
                # Energy
                "power", "energy", "solar", "wind", "hydro", "utility",
                # Home services
                "internet", "broadband", "isp", "mobile", "phone", "cable",
                "security", "alarm", "surveillance"
            ],
            
            CategoryEnum.SHOPPING: [
                # Store types
                "store", "shop", "mall", "boutique", "outlet", "emporium", "hypermarket",
                # Product categories
                "grocery", "electronics", "furniture", "apparel", "footwear", "jewelry",
                # Retailers
                "walmart", "target", "amazon", "flipkart", "best buy", "ikea",
                # Shopping actions
                "purchase", "order", "checkout", "cart", "retail"
            ],
            
            CategoryEnum.ENTERTAINMENT: [
                # Venues
                "cinema", "theater", "stadium", "arena", "club", "casino",
                # Events
                "concert", "festival", "exhibition", "fair", "show", "performance",
                # Activities
                "gaming", "arcade", "bowling", "pool", "darts", "karting",
                # Media
                "netflix", "spotify", "youtube", "prime video", "disney+"
            ],
            
            CategoryEnum.HEALTH: [
                # Facilities
                "hospital", "clinic", "pharmacy", "lab", "diagnostic",
                # Professionals
                "doctor", "dentist", "physician", "therapist", "psychologist",
                # Services
                "checkup", "vaccine", "scan", "x-ray", "surgery", "treatment",
                # Products
                "medicine", "drug", "vitamin", "supplement", "first aid"
            ]
        }
        self.template ="""
                        You will be given OCR text from a receipt or invoice.
                        Extract the following fields from the text:
                        - Vendor Name
                        - Date
                        - Total Amount
                        - Category (food, transport, utilities, shopping, entertainment, health, others)
                        - Description (a short summary including important details)

                        Return the output strictly in this format:
                        <vendor>...</vendor>
                        <date>...</date>
                        <amount>...</amount>
                        <category>...</category>
                        <description>...</description>

                        Text:
                        {text}
                        """

    def process_uploaded_file(self, file_bytes: bytes, file_extension: str) -> Dict:
        try:
            text = self._extract_text(file_bytes, file_extension)
            extracted_data = self._parse_receipt_text(text)
            extracted_data["raw_text"] = extracted_data.get("description")
            validated_data = self._validate_extracted_data(extracted_data)
            return validated_data
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            raise

    def _extract_text(self, file_bytes: bytes, file_extension: str) -> str:
        try:
            reader = easyocr.Reader(['en'], gpu=False)
            if file_extension.lower() in ('.jpg', '.jpeg', '.png'):
                image = Image.open(BytesIO(file_bytes))
                result = reader.readtext(np.array(image), detail=0, paragraph=True)
                return "\n".join(result)
            elif file_extension.lower() == '.pdf':
                pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
                text_blocks = []
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_blocks.append(page_text)
                text = "\n".join(text_blocks).strip()
                if not text or len(text) < 10:
                    images = convert_from_bytes(file_bytes)
                    ocr_blocks = []
                    for img in images:
                        result = reader.readtext(np.array(img), detail=0, paragraph=True)
                        ocr_blocks.append("\n".join(result))
                    text = "\n".join(ocr_blocks)
                return text
            elif file_extension.lower() == '.txt':
                return file_bytes.decode('utf-8')
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            raise

    def _parse_receipt_text(self, text: str) -> Dict:
        prompt = PromptTemplate.from_template(self.template)

        llm = ChatGroq(
            model="llama3-70b-8192",
            api_key=self.groq_api_key,
        )
        chain: RunnableSequence = prompt | llm

        response = chain.invoke({"text": text})
        if hasattr(response, "content"):
            response_text = response.content
        else:
            response_text = str(response)

        vendor = re.search(r"<vendor>(.*?)</vendor>", response_text).group(1)
        date = re.search(r"<date>(.*?)</date>", response_text).group(1)
        amount = re.search(r"<amount>(.*?)</amount>", response_text).group(1)
        category = re.search(r"<category>(.*?)</category>", response_text).group(1)
        description = re.search(r"<description>(.*?)</description>", response_text).group(1)

        return {
            "vendor_name": vendor,
            "date": date,
            "amount": amount,
            "category": category,
            "description": description
        }
    
    def _parse_date_string(self, date_str: str) -> date:
        """Parse various date string formats to a Python date object."""
        try:
            dt = parser.parse(date_str)
            return dt.date()
        except Exception as e:
            logger.error(f"Date parsing failed: {e}")
            return date.today() 

    def _validate_extracted_data(self, data: Dict) -> Dict:
        try:
            category_value = data["category"]
            if isinstance(category_value, str):
                category_enum = None
                for c in CategoryEnum:
                    if c.value.lower() == category_value.lower():
                        category_enum = c
                        break
                if category_enum is None:
                    category_enum = CategoryEnum.OTHER
            else:
                category_enum = category_value

            amount_value = data["amount"]
            if isinstance(amount_value, str):
                amount_value = re.sub(r"[^\d\.\-]", "", amount_value)
                amount_value = amount_value.replace(",", "")
                amount_value = float(amount_value)
            else:
                amount_value = float(amount_value)

            parsed_date = self._parse_date_string(data["date"])
            vendor_data = VendorBase(name=data["vendor_name"], category=category_enum)
            logger.info(f"Parsed data before validation: {data}")
            bill_data = BillEntryBase(
                vendor_id=0,
                amount=amount_value,
                transaction_date=parsed_date,
                description=data.get("raw_text", "")
            )
            return {
                "vendor": vendor_data.dict(),
                "bill": bill_data.dict()
            }
        except ValidationError as e:
            logger.error(f"Data validation failed: {e}")
            raise

    def save_extracted_data(self, extracted_data: Dict, file_reference: str) -> Tuple[bool, str]:
        """Save validated data to database"""
        try:
            vendor_data = extracted_data["vendor"]
            if vendor_data.get("category") and isinstance(vendor_data["category"], CategoryEnum):
                vendor_data["category"] = vendor_data["category"].value
            created, vendor = self.db_handler.add_vendor(vendor_data)
            bill_data = extracted_data["bill"]
            bill_data["vendor_id"] = vendor.id
            bill_data["file_reference"] = file_reference
            self.db_handler.add_bill(bill_data)
            return True, "Data saved successfully"
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            return False, str(e)


    def search_bills(
        self,
        query: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category: Optional[CategoryEnum] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        limit: int = 50,
        sort_by: str = "date",         
        sort_desc: bool = True         
    ) -> List[Dict]:
        """Optimized vendor search with hashed indexing and efficient sorting"""
        bills = self.db_handler.get_bills(
            start_date=start_date,
            end_date=end_date,
            category=category.value if isinstance(category, CategoryEnum) else category,
            min_amount=min_amount,
            max_amount=max_amount,
            limit=limit
        )
        vendor_map = {}
        results = []
        for bill in bills:
            vendor_name = (bill.vendor.name or "").lower()
            bill_dict = {
                "id": bill.id,
                "vendor": bill.vendor.name if bill.vendor else "",
                "amount": bill.amount,
                "date": bill.transaction_date,
                "category": bill.vendor.category if bill.vendor else "",
                "description": bill.description,
                "file_reference": bill.file_reference
            }
            results.append(bill_dict)
            if vendor_name not in vendor_map:
                vendor_map[vendor_name] = []
            vendor_map[vendor_name].append(bill_dict)

        if query:
            query = query.lower().strip()
            filtered_results = []
            for vendor_key in vendor_map:
                if query in vendor_key:
                    filtered_results.extend(vendor_map[vendor_key])
            results = filtered_results

        if sort_by in {"vendor", "amount", "date", "category"}:
            results = sorted(
                results,
                key=lambda x: (
                    x[sort_by] if x[sort_by] is not None else (date.min if sort_by == "date" else "")
                ),
                reverse=sort_desc
            )

        return results


    def get_spending_analytics(self, time_period: str = "monthly") -> Dict:
        if time_period == "monthly":
            data = self.db_handler.get_monthly_spending()
            return {
                "labels": [item[0] for item in data],
                "amounts": [float(item[1]) for item in data]
            }
        elif time_period == "category":
            data = self.db_handler.get_spending_by_category(
                start_date=date(date.today().year, 1, 1),
                end_date=date.today()
            )
            return {
                "categories": [item[0] if item[0] else "Other" for item in data],
                "amounts": [float(item[1]) for item in data]
            }
        else:
            raise ValueError("Invalid time period specified")

    def get_statistics(self) -> Dict:
        bills = self.db_handler.get_bills(limit=1000)
        amounts = [bill.amount for bill in bills]
        
        if not amounts:
            return {}
        
        return {
            "total": sum(amounts),
            "average": statistics.mean(amounts),
            "median": statistics.median(amounts),
            "min": min(amounts),
            "max": max(amounts),
            "count": len(amounts)
        }

    def export_to_dataframe(self) -> pd.DataFrame:
        bills = self.db_handler.get_bills(limit=1000)
        data = []   
        for bill in bills:
            data.append({
                "Date": bill.transaction_date,
                "Vendor": bill.vendor.name,
                "Amount": bill.amount,
                "Category": bill.vendor.category if bill.vendor.category else None,
                "Description": bill.description
            })   
        return pd.DataFrame(data)