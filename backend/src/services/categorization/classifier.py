# backend/src/services/categorization/classifier.py
import getpass
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json
import os

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter your OpenAI API key: ")

class ExpenseCategory(str, Enum):
    GROCERIES = "groceries"
    HOUSEHOLD = "household"
    PERSONAL_CARE = "personal_care"
    HEALTH = "health"
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    ENTERTAINMENT = "entertainment"
    DINING = "dining"
    PETS = "pets"
    TRANSPORTATION = "transportation"
    UTILITIES = "utilities"
    OFFICE = "office"
    MISCELLANEOUS = "miscellaneous"

@dataclass
class ClassifiedItem:
    description: str
    category: ExpenseCategory
    confidence: float
    reasoning: str
    original_price: float

class ExpenseClassifier:
    def __init__(self, api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",  # Using GPT-4o-mini for better accuracy
            temperature=0.1
        ) 
        # Create detailed classification prompt
        self.prompt = ChatPromptTemplate.from_template(
            """You are an expert expense classifier with deep knowledge of retail items and spending patterns.

                Available Categories:
                {category_descriptions}

                Store Context:
                Store Name: {store_name}
                Store Type: {store_type}
                Total Purchase Amount: ${total_amount}

                Items to Classify:
                {items}

                For each item, analyze:
                1. The item description and price
                2. The store context
                3. Common use cases and patterns
                4. Similar items and their typical categories

                Provide a detailed classification in JSON format where each item has:
                - "description": The original item description
                - "category": The most appropriate category (use provided category names exactly)
                - "confidence": Confidence score (0.0-1.0)
                - "reasoning": Detailed explanation of why this category was chosen
                - "alternative_category": Second most likely category if applicable

                Example response format:
                {
                    "items": [
                        {
                            "description": "Milk 2%",
                            "category": "groceries",
                            "confidence": 0.95,
                            "reasoning": "Dairy product primarily used for food consumption, typical grocery item",
                            "alternative_category": "none"
                        }
                    ]
                }

                Remember:
                - Consider the store type and context
                - Look for specific item indicators in descriptions
                - Account for price points in classification
                - Be specific in reasoning
                - Maintain consistent category names
                """
        )

    def _get_store_type(self, store_name: str) -> str:
        """Determine store type based on store name."""
        store_name_lower = store_name.lower()
        
        store_types = {
            'grocery': ['walmart', 'kroger', 'safeway', 'trader', 'whole foods', 'aldi', 'food'],
            'pharmacy': ['cvs', 'walgreens', 'rite aid', 'pharmacy'],
            'department': ['target', 'macy', 'nordstrom', 'dillard'],
            'electronics': ['best buy', 'apple', 'micro center'],
            'office': ['office depot', 'staples', 'office max'],
            'pet': ['petco', 'petsmart', 'pet'],
            'home': ['home depot', 'lowe', 'ikea', 'bed bath'],
            'clothing': ['gap', 'old navy', 'h&m', 'zara'],
        }
        
        for store_type, patterns in store_types.items():
            if any(pattern in store_name_lower for pattern in patterns):
                return f"{store_type.title()} Store"
        
        return "General Retail Store"

    def _get_category_descriptions(self) -> str:
        """Get detailed descriptions for each category."""
        descriptions = {
            ExpenseCategory.GROCERIES: "Food items, beverages, ingredients, snacks, and consumable household supplies",
            ExpenseCategory.HOUSEHOLD: "Cleaning supplies, home maintenance items, storage solutions, and basic home goods",
            ExpenseCategory.PERSONAL_CARE: "Hygiene products, cosmetics, skincare, haircare, and personal grooming items",
            ExpenseCategory.HEALTH: "Medications, supplements, first aid supplies, and health-related items",
            ExpenseCategory.ELECTRONICS: "Electronic devices, accessories, cables, and technology-related items",
            ExpenseCategory.CLOTHING: "Apparel, shoes, accessories, and clothing-related items",
            ExpenseCategory.ENTERTAINMENT: "Games, toys, books, movies, and recreational items",
            ExpenseCategory.DINING: "Prepared foods, restaurant meals, and ready-to-eat items",
            ExpenseCategory.PETS: "Pet food, supplies, toys, and pet care items",
            ExpenseCategory.TRANSPORTATION: "Fuel, vehicle supplies, transit passes, and transportation-related items",
            ExpenseCategory.UTILITIES: "Utility payments, service charges, and related supplies",
            ExpenseCategory.OFFICE: "Office supplies, stationery, and work-related items",
            ExpenseCategory.MISCELLANEOUS: "Items that don't clearly fit into other categories"
        }
        
        return "\n".join([f"- {cat.value}: {desc}" for cat, desc in descriptions.items()])

    async def classify_items(
        self, 
        items: List[Dict], 
        store_name: str,
        total_amount: float
    ) -> List[ClassifiedItem]:
        """Classify items using LLM with enhanced context."""
        try:
            # Prepare store context
            store_type = self._get_store_type(store_name)
            
            # Format items for prompt
            items_text = "\n".join([
                f"- {item['description']}: ${item['price']:.2f}"
                for item in items
            ])
            
            # Get LLM response
            response = await self.llm.ainvoke(
                self.prompt.format(
                    category_descriptions=self._get_category_descriptions(),
                    store_name=store_name,
                    store_type=store_type,
                    total_amount=total_amount,
                    items=items_text,
                    
                )
                
            )
            console.print("Items classified")
            # Parse response
            try:
                classified = json.loads(response)['items']
                
                # Convert to ClassifiedItem objects
                result = []
                for item_data, original_item in zip(classified, items):
                    result.append(ClassifiedItem(
                        description=original_item['description'],
                        category=ExpenseCategory(item_data['category']),
                        confidence=item_data['confidence'],
                        reasoning=item_data['reasoning'],
                        original_price=original_item['price']
                    ))
                console.print("result: ", result)
                return result
                
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error parsing LLM response: {str(e)}")
                return self._generate_fallback_classifications(items)
                
        except Exception as e:
            print(f"Error in LLM classification: {str(e)}")
            return self._generate_fallback_classifications(items)

    def _generate_fallback_classifications(self, items: List[Dict]) -> List[ClassifiedItem]:
        """Generate fallback classification when LLM fails."""
        return [
            ClassifiedItem(
                description=item['description'],
                category=ExpenseCategory.MISCELLANEOUS,
                confidence=0.5,
                reasoning="Fallback classification due to processing error",
                original_price=item['price']
            )
            for item in items
        ]