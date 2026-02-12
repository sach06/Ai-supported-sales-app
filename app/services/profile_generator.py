"""
AI Service for generating customer profiles (Steckbrief) using LLM
"""
import json
import numpy as np
from typing import Dict, Optional
from openai import AzureOpenAI, OpenAI
from app.core.config import settings

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for NumPy types"""
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.generic):
            return obj.item()
        return super(NumpyEncoder, self).default(obj)


class ProfileGeneratorService:
    """Generate comprehensive customer profiles using AI"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client (Azure or Standard)"""
        if settings.use_azure_openai:
            self.client = AzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                timeout=60.0
            )
            self.model = settings.AZURE_OPENAI_DEPLOYMENT
            print("Azure OpenAI client initialized")
        elif settings.use_openai:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = "gpt-4o"
            print("OpenAI client initialized")
        else:
            print("No OpenAI API key configured. Profile generation will be limited.")
    
    def generate_profile(self, customer_data: Dict, web_data: Optional[str] = None) -> Dict:
        """
        Generate a comprehensive customer profile (Steckbrief)
        
        Args:
            customer_data: Dictionary containing CRM, BCG, and installed base data
            web_data: Optional web search results for enrichment
        
        Returns:
            Dictionary with structured profile fields
        """
        if not self.client:
            return self._generate_fallback_profile(customer_data)
        
        # Build context from available data
        context = self._build_context(customer_data, web_data)
        
        # Create prompt for structured profile generation
        prompt = self._create_profile_prompt(context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert business analyst creating detailed customer profiles for B2B sales teams."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            profile_json = json.loads(response.choices[0].message.content)
            return profile_json
            
        except Exception as e:
            print(f"Error generating profile: {e}")
            return self._generate_fallback_profile(customer_data)
    
    def _build_context(self, customer_data: Dict, web_data: Optional[str]) -> str:
        """Build context string from available data"""
        context_parts = []
        
        if 'crm' in customer_data:
            context_parts.append("CRM DATA:\n" + json.dumps(customer_data['crm'], indent=2, cls=NumpyEncoder))
        
        if 'bcg' in customer_data:
            context_parts.append("MARKET DATA:\n" + json.dumps(customer_data['bcg'], indent=2, cls=NumpyEncoder))
        
        if 'installed_base' in customer_data:
            context_parts.append(f"INSTALLED BASE:\n{len(customer_data['installed_base'])} equipment records")
            context_parts.append(json.dumps(customer_data['installed_base'][:3], indent=2, cls=NumpyEncoder))  # Sample
        
        
        if web_data:
            context_parts.append(f"WEB RESEARCH:\n{web_data}")
        
        return "\n\n".join(context_parts)

    
    def _create_profile_prompt(self, context: str) -> str:
        """Create the prompt for profile generation"""
        return f"""Based on the following customer data, generate a comprehensive customer profile (Steckbrief) in JSON format.

{context}

Generate a JSON object with the following structure:
{{
    "basic_data": {{
        "name": "Company name",
        "hq_address": "Headquarters address",
        "latitude": "Latitude as float or null",
        "longitude": "Longitude as float or null",
        "owner": "Owner/Parent company",
        "management": "Key management personnel (CEO, CFO, etc.)",
        "ceo": "Specific name of the CEO",
        "fte": "Number of employees (total FTE)",
        "financials": "Financial status/revenue (latest available)",
        "buying_center": "Buying center information",
        "company_focus": "Company focus, vision, strategy",
        "embargos_esg": "Any embargos or ESG concerns",
        "frame_agreements": "Existing frame agreements",
        "recent_facts": "Any notable recent news, mergers, or strategic shifts from the last 1-2 years",
        "ownership_history": "Brief ownership history with dates (e.g., Pre-2016: X, 2016-2019: Y, 2020-present: Z)"
    }},
    "locations": [
        {{
            "address": "Location address",
            "city": "City",
            "country": "Country",
            "latitude": "Latitude as float or null",
            "longitude": "Longitude as float or null",
            "installed_base": [
                {{
                    "equipment_type": "Type of equipment",
                    "manufacturer": "OEM/Manufacturer",
                    "year_of_startup": "Year",
                    "status": "Operational/Idle"
                }}
            ],
            "final_products": "Products manufactured as list or string",
            "tons_per_year": "Production capacity"
        }}
    ],
    "history": {{
        "latest_projects": "Recent projects",
        "realized_projects": "Completed projects",
        "crm_rating": "CRM rating",
        "key_person": "Key contact person",
        "sms_relationship": "Best SMS contact/relationship",
        "latest_visits": "Recent visits"
    }},
    "context": {{
        "end_customer": "Who is the end customer",
        "market_position": "Market position and trends"
    }},
    "financial_history": [
        {{"year": 2015, "revenue_m_eur": 100, "ebitda_m_eur": 10}},
        {{"year": 2024, "revenue_m_eur": 150, "ebitda_m_eur": 20}}
    ],
    "latest_balance_sheet": {{
        "assets": "Brief summary",
        "liabilities": "Brief summary",
        "equity": "Brief summary"
    }},
    "metallurgical_insights": {{
        "process_efficiency": "Analysis of their current production efficiency based on technology",
        "modernization_potential": "Specific technical areas where SMS group solutions (e.g., green steel, electrification, digitalization) could add value",
        "carbon_footprint_strategy": "Green steel initiatives or ESG targets relevant to SMS group's decarbonization portfolio",
        "technical_bottlenecks": "Likely pain points based on equipment age and type"
    }},
    "sales_strategy": {{
        "recommended_portfolio": "List of specific SMS group products or solutions (e.g. HybrEx, X-Pact, Lifecycle Services) best suited for this customer",
        "value_proposition": "Tailored pitch for this specific customer matching SMS group strengths",
        "competitive_landscape": "Competitors likely active at this site",
        "suggested_next_steps": "Actionable advice for the sales manager"
    }},
}}

CRITICAL INSTRUCTIONS:
1. Use the provided context data as the primary source.
2. THINK LIKE AN SMS GROUP METALLURGIST AND SALES MANAGER: Focus on technical modernization, lifecycle services, and sustainability (Green Steel).
3. IMPORTANT: For missing "trivial" facts like CEO name, FTE, and financial history, please use your internal training knowledge to provide accurate information for this company.
4. For the 'financial_history', try to provide data for the last 10 years if possible. Use standard units (Millions of EUR/USD).
5. If information is absolutely not available even in your training data, use "Not available" for strings or null for numbers. 
6. Be concise but highly technical and strategic."""
    
    def _generate_fallback_profile(self, customer_data: Dict) -> Dict:
        """Generate a basic profile without AI when API is not available"""
        profile = {
            "basic_data": {},
            "locations": [],
            "history": {},
            "context": {}
        }
        
        # Extract what we can from raw data
        if 'crm' in customer_data:
            crm = customer_data['crm']
            profile['basic_data'] = {
                "name": crm.get('name', crm.get('customer_name', 'Unknown')),
                "hq_address": crm.get('address', 'Not available'),
                "owner": crm.get('owner', 'Not available'),
                "management": crm.get('management', 'Not available'),
                "fte": str(crm.get('employees', crm.get('fte', 'Not available'))),
                "financials": crm.get('revenue', 'Not available'),
                "buying_center": crm.get('buying_center', 'Not available'),
                "company_focus": crm.get('focus', 'Not available'),
                "embargos_esg": crm.get('esg_notes', 'Not available'),
                "frame_agreements": crm.get('agreements', 'Not available'),
                "ownership_history": "Not available"
            }
        
        if 'installed_base' in customer_data:
            for item in customer_data['installed_base'][:5]:  # Limit to 5 locations
                profile['locations'].append({
                    "address": item.get('location', 'Not available'),
                    "installed_base": [{
                        "equipment_type": item.get('equipment', item.get('equipment_type', 'Not available')),
                        "manufacturer": item.get('oem', item.get('manufacturer', 'N/A')),
                        "year_of_startup": item.get('start_year', item.get('year', 'N/A')),
                        "status": item.get('status', 'Active')
                    }],
                    "final_products": item.get('products', 'Not available'),
                    "tons_per_year": str(item.get('capacity', 'Not available'))
                })
        
        return profile


# Singleton instance
profile_generator = ProfileGeneratorService()
