"""
Enhanced Invoice Extraction Agent for the Agentic AI System
"""
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from .base_agent import BaseAgent
from ..utils.message_queue import MessageType, MessagePriority, create_anomaly_alert
from ..config.settings import AGENT_CONFIG

class InvoiceExtractionAgent(BaseAgent):
    """Specialized agent for extracting and validating invoice data"""
    
    def __init__(self, agent_id: str = "extraction_agent"):
        config = AGENT_CONFIG.get("extraction_agent", {})
        super().__init__(agent_id, config.get("name", "Invoice Extraction Agent"), config)
        
        # Invoice-specific knowledge
        self.required_fields = [
            "invoice_number", "invoice_date", "total_amount", 
            "buyers_order_number", "vendor_name", "buyer_name"
        ]
        
        self.field_patterns = {
            "invoice_number": r"(?:INV|INVOICE|BILL)[\s\-]*([A-Z0-9\-/]+)",
            "invoice_date": r"(?:DATE|DATED)[\s:]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            "total_amount": r"(?:TOTAL|AMOUNT|RS\.?)[\s:]*([\d,]+\.?\d*)",
            "buyers_order_number": r"(?:ORDER|PO|PURCHASE ORDER)[\s#]*([A-Z0-9\-]+)",
            "vendor_name": r"(?:SELLER|VENDOR|FROM)[\s:]*([A-Z\s&]+)",
            "buyer_name": r"(?:BUYER|TO|BILL TO)[\s:]*([A-Z\s&]+)"
        }
        
        self.logger.info(f"Invoice Extraction Agent initialized with {len(self.required_fields)} required fields")
    
    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process invoice extraction task"""
        start_time = datetime.now()
        
        try:
            self.status = AgentStatus.PROCESSING
            self.logger.info(f"Processing invoice extraction task: {task_data.get('task_id', 'Unknown')}")
            
            # Extract invoice data
            invoice_data = self._extract_invoice_data(task_data)
            
            # Validate extracted data
            validation_result = self.validate_data(invoice_data)
            
            # Detect anomalies
            anomalies = self.detect_anomalies(invoice_data)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(invoice_data, validation_result, anomalies)
            
            # Prepare result
            result = {
                "extraction_result": invoice_data,
                "validation_result": validation_result,
                "anomalies": anomalies,
                "confidence": confidence,
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "status": "completed"
            }
            
            # Update metrics
            self.metrics.record_task_completion(result["processing_time"], confidence)
            
            # Send anomaly alerts if any
            if anomalies:
                for anomaly in anomalies:
                    alert_msg = create_anomaly_alert(
                        sender_id=self.agent_id,
                        recipient_id="manager_agent",
                        anomaly_type=anomaly["type"],
                        anomaly_data=anomaly,
                        severity=anomaly.get("severity", "medium")
                    )
                    self.message_queue.send_message(alert_msg)
            
            self.logger.info(f"Invoice extraction completed with confidence: {confidence:.2f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing invoice extraction task: {e}")
            self.metrics.record_task_failure(str(e))
            self.status = AgentStatus.ERROR
            return {
                "error": str(e),
                "status": "failed",
                "processing_time": (datetime.now() - start_time).total_seconds()
            }
        finally:
            self.status = AgentStatus.IDLE
    
    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate extracted invoice data"""
        validation_result = {
            "is_valid": True,
            "missing_fields": [],
            "field_quality": {},
            "overall_score": 0.0,
            "warnings": []
        }
        
        # Check required fields
        for field in self.required_fields:
            if field not in data or not data[field]:
                validation_result["missing_fields"].append(field)
                validation_result["is_valid"] = False
        
        # Validate field quality
        for field, value in data.items():
            quality_score = self._assess_field_quality(field, value)
            validation_result["field_quality"][field] = quality_score
        
        # Calculate overall score
        if validation_result["field_quality"]:
            validation_result["overall_score"] = sum(validation_result["field_quality"].values()) / len(validation_result["field_quality"])
        
        # Add warnings for low quality fields
        for field, score in validation_result["field_quality"].items():
            if score < 0.7:
                validation_result["warnings"].append(f"Low quality field: {field} (score: {score:.2f})")
        
        return validation_result
    
    def detect_anomalies(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in invoice data"""
        anomalies = []
        
        # Check for missing critical fields
        if not data.get("invoice_number"):
            anomalies.append({
                "type": "missing_invoice_number",
                "severity": "critical",
                "description": "Invoice number is missing",
                "field": "invoice_number"
            })
        
        if not data.get("total_amount"):
            anomalies.append({
                "type": "missing_total_amount",
                "severity": "critical",
                "description": "Total amount is missing",
                "field": "total_amount"
            })
        
        # Check for unusual amounts
        if data.get("total_amount"):
            try:
                amount = float(str(data["total_amount"]).replace(",", ""))
                if amount <= 0:
                    anomalies.append({
                        "type": "invalid_amount",
                        "severity": "high",
                        "description": f"Invalid amount: {amount}",
                        "field": "total_amount",
                        "value": amount
                    })
                elif amount > 1000000:  # Flag very high amounts
                    anomalies.append({
                        "type": "unusually_high_amount",
                        "severity": "medium",
                        "description": f"Unusually high amount: {amount}",
                        "field": "total_amount",
                        "value": amount
                    })
            except (ValueError, TypeError):
                anomalies.append({
                    "type": "invalid_amount_format",
                    "severity": "high",
                    "description": "Amount format is invalid",
                    "field": "total_amount",
                    "value": data["total_amount"]
                })
        
        # Check for date anomalies
        if data.get("invoice_date"):
            try:
                invoice_date = datetime.strptime(data["invoice_date"], "%Y-%m-%d")
                current_date = datetime.now()
                if invoice_date > current_date:
                    anomalies.append({
                        "type": "future_date",
                        "severity": "medium",
                        "description": "Invoice date is in the future",
                        "field": "invoice_date",
                        "value": data["invoice_date"]
                    })
                elif (current_date - invoice_date).days > 365:
                    anomalies.append({
                        "type": "old_invoice",
                        "severity": "low",
                        "description": "Invoice is more than 1 year old",
                        "field": "invoice_date",
                        "value": data["invoice_date"]
                    })
            except ValueError:
                anomalies.append({
                    "type": "invalid_date_format",
                    "severity": "medium",
                    "description": "Invalid date format",
                    "field": "invoice_date",
                    "value": data["invoice_date"]
                })
        
        # Check for vendor/buyer mismatches
        if data.get("vendor_name") and data.get("buyer_name"):
            if data["vendor_name"] == data["buyer_name"]:
                anomalies.append({
                    "type": "vendor_buyer_same",
                    "severity": "high",
                    "description": "Vendor and buyer are the same",
                    "fields": ["vendor_name", "buyer_name"],
                    "values": [data["vendor_name"], data["buyer_name"]]
                })
        
        return anomalies
    
    def _extract_invoice_data(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract invoice data from the task"""
        invoice_data = {}
        
        # Handle different input types
        if "file_path" in task_data:
            invoice_data = self._extract_from_file(task_data["file_path"])
        elif "text_content" in task_data:
            invoice_data = self._extract_from_text(task_data["text_content"])
        elif "json_data" in task_data:
            invoice_data = self._extract_from_json(task_data["json_data"])
        else:
            raise ValueError("No valid input data provided")
        
        # Clean and normalize data
        invoice_data = self._clean_extracted_data(invoice_data)
        
        return invoice_data
    
    def _extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """Extract data from file (PDF, image, etc.)"""
        # For now, we'll assume JSON files
        # In production, this would integrate with OCR/PDF processing
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return {}
    
    def _extract_from_text(self, text_content: str) -> Dict[str, Any]:
        """Extract data from text content using pattern matching"""
        extracted_data = {}
        
        for field, pattern in self.field_patterns.items():
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                extracted_data[field] = match.group(1).strip()
        
        return extracted_data
    
    def _extract_from_json(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from JSON structure"""
        # Map common JSON fields to our standard format
        field_mapping = {
            "invoice_number": ["invoice_number", "invoice_no", "inv_no", "bill_number"],
            "invoice_date": ["invoice_date", "date", "bill_date", "dated"],
            "total_amount": ["total_amount", "total", "amount", "grand_total"],
            "buyers_order_number": ["buyers_order_number", "po_number", "order_number", "purchase_order"],
            "vendor_name": ["vendor_name", "seller_name", "from", "supplier"],
            "buyer_name": ["buyer_name", "customer_name", "to", "bill_to"]
        }
        
        extracted_data = {}
        
        for standard_field, possible_fields in field_mapping.items():
            for field in possible_fields:
                if field in json_data and json_data[field]:
                    extracted_data[standard_field] = json_data[field]
                    break
        
        return extracted_data
    
    def _clean_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize extracted data"""
        cleaned_data = {}
        
        for field, value in data.items():
            if isinstance(value, str):
                # Remove extra whitespace
                cleaned_value = re.sub(r'\s+', ' ', value.strip())
                # Convert to standard date format if it's a date
                if field in ["invoice_date", "due_date"]:
                    cleaned_value = self._standardize_date(cleaned_value)
                # Convert to standard amount format if it's an amount
                elif field in ["total_amount", "subtotal", "tax_amount"]:
                    cleaned_value = self._standardize_amount(cleaned_value)
                
                cleaned_data[field] = cleaned_value
            else:
                cleaned_data[field] = value
        
        return cleaned_data
    
    def _standardize_date(self, date_str: str) -> str:
        """Convert various date formats to YYYY-MM-DD"""
        try:
            # Handle common date formats
            date_formats = [
                "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d",
                "%d-%m-%y", "%d/%m/%y", "%y-%m-%d", "%y/%m/%d"
            ]
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            
            # If no format matches, return original
            return date_str
        except Exception:
            return date_str
    
    def _standardize_amount(self, amount_str: str) -> str:
        """Convert various amount formats to standard decimal format"""
        try:
            # Remove currency symbols and commas
            cleaned = re.sub(r'[^\d.,]', '', str(amount_str))
            # Handle different decimal separators
            if ',' in cleaned and '.' in cleaned:
                # Format like "1,234.56"
                cleaned = cleaned.replace(',', '')
            elif ',' in cleaned:
                # Format like "1,234" or "1,234,56"
                if cleaned.count(',') == 1 and len(cleaned.split(',')[1]) == 2:
                    # Likely "1,234,56" format
                    cleaned = cleaned.replace(',', '.')
                else:
                    # Likely "1,234" format
                    cleaned = cleaned.replace(',', '')
            
            return cleaned
        except Exception:
            return str(amount_str)
    
    def _assess_field_quality(self, field: str, value: Any) -> float:
        """Assess the quality of an extracted field"""
        if not value:
            return 0.0
        
        # Base quality score
        quality = 0.5
        
        # Field-specific quality checks
        if field == "invoice_number":
            if re.match(r'^[A-Z0-9\-/]+$', str(value)):
                quality += 0.3
            if len(str(value)) >= 5:
                quality += 0.2
        
        elif field == "invoice_date":
            try:
                datetime.strptime(str(value), "%Y-%m-%d")
                quality += 0.4
            except ValueError:
                quality += 0.1
        
        elif field == "total_amount":
            try:
                amount = float(str(value).replace(",", ""))
                if amount > 0:
                    quality += 0.4
            except ValueError:
                quality += 0.1
        
        elif field in ["vendor_name", "buyer_name"]:
            if len(str(value)) >= 3:
                quality += 0.3
            if re.search(r'[A-Z]', str(value)):
                quality += 0.2
        
        return min(quality, 1.0)
    
    def _calculate_confidence(self, data: Dict[str, Any], validation: Dict[str, Any], anomalies: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score"""
        # Base confidence from validation
        base_confidence = validation.get("overall_score", 0.0)
        
        # Penalty for anomalies
        anomaly_penalty = 0.0
        for anomaly in anomalies:
            severity_weights = {"low": 0.05, "medium": 0.1, "high": 0.2, "critical": 0.3}
            penalty = severity_weights.get(anomaly.get("severity", "medium"), 0.1)
            anomaly_penalty += penalty
        
        # Penalty for missing required fields
        missing_penalty = len(validation.get("missing_fields", [])) * 0.15
        
        # Calculate final confidence
        confidence = base_confidence - anomaly_penalty - missing_penalty
        
        return max(0.0, min(1.0, confidence))
    
    def get_extraction_capabilities(self) -> Dict[str, Any]:
        """Get information about extraction capabilities"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "supported_formats": ["JSON", "Text", "PDF", "Image"],
            "required_fields": self.required_fields,
            "field_patterns": list(self.field_patterns.keys()),
            "confidence_threshold": self.decision_threshold,
            "processing_capabilities": [
                "Pattern-based extraction",
                "Data validation",
                "Anomaly detection",
                "Data cleaning and normalization"
            ]
        }