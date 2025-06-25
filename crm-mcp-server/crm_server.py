#!/usr/bin/env python3

import asyncio
import json
import sqlite3
import uuid
from datetime import datetime
from typing import Any

import mcp.types as types
from mcp.server import Server
import mcp.server.stdio

# Database path
DB_PATH = "crm_database.db"

# Create server instance
app = Server("crm-server")

class CRMDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the CRM database with proper schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create customers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id TEXT PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    phone TEXT,
                    company TEXT,
                    industry TEXT,
                    annual_revenue REAL,
                    employee_count INTEGER,
                    status TEXT DEFAULT 'active',
                    lead_source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create interactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    interaction_type TEXT NOT NULL,
                    subject TEXT,
                    notes TEXT,
                    interaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers (id)
                )
            """)
            
            # Create deals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deals (
                    id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    deal_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    stage TEXT DEFAULT 'prospecting',
                    probability REAL DEFAULT 0.0,
                    expected_close_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers (id)
                )
            """)
            
            conn.commit()
    
    def execute_query(self, query: str, params: tuple = ()) -> list[dict[str, Any]]:
        """Execute a SELECT query safely with parameterized inputs."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_write(self, query: str, params: tuple = ()) -> str:
        """Execute INSERT/UPDATE/DELETE queries safely."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid

# Initialize database
db = CRMDatabase(DB_PATH)

@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available CRM tools."""
    return [
        types.Tool(
            name="add_customer",
            description="Add a new customer to the CRM system",
            inputSchema={
                "type": "object",
                "properties": {
                    "first_name": {"type": "string", "description": "Customer's first name"},
                    "last_name": {"type": "string", "description": "Customer's last name"},
                    "email": {"type": "string", "description": "Customer's email address"},
                    "phone": {"type": "string", "description": "Customer's phone number"},
                    "company": {"type": "string", "description": "Customer's company name"},
                    "industry": {"type": "string", "description": "Customer's industry"},
                    "annual_revenue": {"type": "number", "description": "Company's annual revenue"},
                    "employee_count": {"type": "integer", "description": "Number of employees"},
                    "lead_source": {"type": "string", "description": "How the lead was acquired"}
                },
                "required": ["first_name", "last_name", "email"]
            }
        ),
        types.Tool(
            name="search_customers",
            description="Search for customers by name, email, company, or industry",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_term": {"type": "string", "description": "The term to search for"},
                    "search_field": {"type": "string", "description": "Field to search in", "enum": ["all", "name", "email", "company", "industry"]}
                },
                "required": ["search_term"]
            }
        ),
        types.Tool(
            name="get_customer",
            description="Get detailed information about a specific customer",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "The unique customer identifier"}
                },
                "required": ["customer_id"]
            }
        ),
        types.Tool(
            name="add_interaction",
            description="Add a customer interaction record",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "The customer's unique identifier"},
                    "interaction_type": {"type": "string", "description": "Type of interaction (call, email, meeting, etc.)"},
                    "subject": {"type": "string", "description": "Brief subject of the interaction"},
                    "notes": {"type": "string", "description": "Detailed notes about the interaction"}
                },
                "required": ["customer_id", "interaction_type"]
            }
        ),
        types.Tool(
            name="add_deal",
            description="Add a new deal for a customer",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "The customer's unique identifier"},
                    "deal_name": {"type": "string", "description": "Name/description of the deal"},
                    "value": {"type": "number", "description": "Monetary value of the deal"},
                    "stage": {"type": "string", "description": "Current stage", "enum": ["prospecting", "qualification", "proposal", "negotiation", "closed-won", "closed-lost"]},
                    "probability": {"type": "number", "description": "Probability of closing (0.0 to 1.0)"},
                    "expected_close_date": {"type": "string", "description": "Expected close date (YYYY-MM-DD format)"}
                },
                "required": ["customer_id", "deal_name", "value"]
            }
        ),
        types.Tool(
            name="populate_sample_data",
            description="Populate the database with sample customer data for testing",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="analyze_customers_by_industry",
            description="Analyze customer distribution by industry",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="analyze_deal_pipeline",
            description="Analyze the sales deal pipeline",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="get_top_customers_by_revenue",
            description="Get top customers by annual revenue",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="get_recent_interactions",
            description="Get recent customer interactions",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Number of days back to search (default: 7)"}
                }
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    """Handle tool calls."""
    
    if name == "add_customer":
        customer_id = str(uuid.uuid4())
        try:
            query = """
                INSERT INTO customers 
                (id, first_name, last_name, email, phone, company, industry, 
                 annual_revenue, employee_count, lead_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                customer_id,
                arguments.get("first_name", ""),
                arguments.get("last_name", ""),
                arguments.get("email", ""),
                arguments.get("phone", ""),
                arguments.get("company", ""),
                arguments.get("industry", ""),
                arguments.get("annual_revenue", 0.0),
                arguments.get("employee_count", 0),
                arguments.get("lead_source", "")
            )
            
            db.execute_write(query, params)
            return [types.TextContent(type="text", text=f"✅ Customer successfully added with ID: {customer_id}")]
            
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: customers.email" in str(e):
                return [types.TextContent(type="text", text=f"❌ Error: Customer with email {arguments.get('email')} already exists")]
            return [types.TextContent(type="text", text=f"❌ Database error: {str(e)}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"❌ Error adding customer: {str(e)}")]
    
    elif name == "search_customers":
        try:
            search_term = arguments["search_term"]
            search_field = arguments.get("search_field", "all")
            
            if search_field == "all":
                query = """
                    SELECT * FROM customers 
                    WHERE first_name LIKE ? OR last_name LIKE ? OR email LIKE ? 
                    OR company LIKE ? OR industry LIKE ?
                    ORDER BY last_name, first_name
                """
                search_pattern = f"%{search_term}%"
                params = (search_pattern, search_pattern, search_pattern, 
                         search_pattern, search_pattern)
            elif search_field == "name":
                query = """
                    SELECT * FROM customers 
                    WHERE first_name LIKE ? OR last_name LIKE ?
                    ORDER BY last_name, first_name
                """
                search_pattern = f"%{search_term}%"
                params = (search_pattern, search_pattern)
            elif search_field == "email":
                query = "SELECT * FROM customers WHERE email LIKE ? ORDER BY email"
                params = (f"%{search_term}%",)
            elif search_field == "company":
                query = "SELECT * FROM customers WHERE company LIKE ? ORDER BY company"
                params = (f"%{search_term}%",)
            elif search_field == "industry":
                query = "SELECT * FROM customers WHERE industry LIKE ? ORDER BY industry"
                params = (f"%{search_term}%",)
            else:
                return [types.TextContent(type="text", text=f"❌ Invalid search field: {search_field}. Use: all, name, email, company, or industry")]
            
            results = db.execute_query(query, params)
            
            if not results:
                return [types.TextContent(type="text", text=f"🔍 No customers found matching '{search_term}' in {search_field}")]
                
            return [types.TextContent(type="text", text=f"🔍 Found {len(results)} customers:\n\n{json.dumps(results, indent=2, default=str)}")]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"❌ Error searching customers: {str(e)}")]
    
    elif name == "get_customer":
        try:
            query = "SELECT * FROM customers WHERE id = ?"
            results = db.execute_query(query, (arguments["customer_id"],))
            
            if not results:
                return [types.TextContent(type="text", text=f"❌ No customer found with ID: {arguments['customer_id']}")]
                
            customer = results[0]
            return [types.TextContent(type="text", text=f"👤 Customer Details:\n\n{json.dumps(customer, indent=2, default=str)}")]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"❌ Error retrieving customer: {str(e)}")]
    
    elif name == "add_interaction":
        interaction_id = str(uuid.uuid4())
        try:
            query = """
                INSERT INTO interactions (id, customer_id, interaction_type, subject, notes)
                VALUES (?, ?, ?, ?, ?)
            """
            params = (
                interaction_id, 
                arguments["customer_id"], 
                arguments["interaction_type"], 
                arguments.get("subject", ""), 
                arguments.get("notes", "")
            )
            
            db.execute_write(query, params)
            return [types.TextContent(type="text", text=f"✅ Interaction successfully added with ID: {interaction_id}")]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"❌ Error adding interaction: {str(e)}")]
    
    elif name == "add_deal":
        deal_id = str(uuid.uuid4())
        try:
            query = """
                INSERT INTO deals (id, customer_id, deal_name, value, stage, probability, expected_close_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                deal_id, 
                arguments["customer_id"], 
                arguments["deal_name"], 
                arguments["value"],
                arguments.get("stage", "prospecting"),
                arguments.get("probability", 0.0),
                arguments.get("expected_close_date", None)
            )
            
            db.execute_write(query, params)
            return [types.TextContent(type="text", text=f"✅ Deal successfully added with ID: {deal_id}")]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"❌ Error adding deal: {str(e)}")]
    
    elif name == "populate_sample_data":
        try:
            sample_customers = [
                ("John", "Doe", "john.doe@techcorp.com", "+1-555-0101", "TechCorp", "Technology", 5000000, 50, "website"),
                ("Jane", "Smith", "jane.smith@retailplus.com", "+1-555-0102", "RetailPlus", "Retail", 2000000, 25, "referral"),
                ("Bob", "Johnson", "bob@manufacturing.com", "+1-555-0103", "ManufacturingCo", "Manufacturing", 10000000, 100, "trade_show"),
                ("Alice", "Williams", "alice@healthsys.com", "+1-555-0104", "HealthSystems", "Healthcare", 15000000, 200, "cold_call"),
                ("Charlie", "Brown", "charlie@fintech.com", "+1-555-0105", "FinTech Solutions", "Financial", 8000000, 75, "linkedin"),
            ]
            
            for customer in sample_customers:
                customer_id = str(uuid.uuid4())
                query = """
                    INSERT OR IGNORE INTO customers 
                    (id, first_name, last_name, email, phone, company, industry, 
                     annual_revenue, employee_count, lead_source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                params = (customer_id,) + customer
                db.execute_write(query, params)
            
            return [types.TextContent(type="text", text="✅ Sample data populated successfully! Added 5 sample customers.")]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"❌ Error populating sample data: {str(e)}")]
    
    elif name == "analyze_customers_by_industry":
        try:
            query = """
                SELECT 
                    industry,
                    COUNT(*) as customer_count,
                    AVG(annual_revenue) as avg_revenue,
                    SUM(annual_revenue) as total_revenue,
                    AVG(employee_count) as avg_employees
                FROM customers 
                WHERE industry != '' 
                GROUP BY industry
                ORDER BY customer_count DESC
            """
            results = db.execute_query(query)
            
            if not results:
                return [types.TextContent(type="text", text="📊 No industry data available")]
                
            return [types.TextContent(type="text", text=f"📊 Customer Analysis by Industry:\n\n{json.dumps(results, indent=2, default=str)}")]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"❌ Error analyzing industries: {str(e)}")]
    
    elif name == "analyze_deal_pipeline":
        try:
            query = """
                SELECT 
                    stage,
                    COUNT(*) as deal_count,
                    SUM(value) as total_value,
                    AVG(value) as avg_deal_size,
                    AVG(probability) as avg_probability,
                    SUM(value * probability) as weighted_value
                FROM deals
                GROUP BY stage
                ORDER BY 
                    CASE stage
                        WHEN 'prospecting' THEN 1
                        WHEN 'qualification' THEN 2
                        WHEN 'proposal' THEN 3
                        WHEN 'negotiation' THEN 4
                        WHEN 'closed-won' THEN 5
                        WHEN 'closed-lost' THEN 6
                        ELSE 7
                    END
            """
            results = db.execute_query(query)
            
            if not results:
                return [types.TextContent(type="text", text="📈 No deals in pipeline")]
                
            return [types.TextContent(type="text", text=f"📈 Deal Pipeline Analysis:\n\n{json.dumps(results, indent=2, default=str)}")]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"❌ Error analyzing pipeline: {str(e)}")]
    
    elif name == "get_top_customers_by_revenue":
        try:
            query = """
                SELECT 
                    first_name,
                    last_name,
                    company,
                    industry,
                    annual_revenue,
                    email
                FROM customers
                WHERE annual_revenue > 0
                ORDER BY annual_revenue DESC
                LIMIT 10
            """
            results = db.execute_query(query)
            
            if not results:
                return [types.TextContent(type="text", text="💰 No customers with revenue data found")]
                
            return [types.TextContent(type="text", text=f"💰 Top Customers by Revenue:\n\n{json.dumps(results, indent=2, default=str)}")]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"❌ Error retrieving top customers: {str(e)}")]
    
    elif name == "get_recent_interactions":
        try:
            days = arguments.get("days", 7)
            query = """
                SELECT 
                    i.*,
                    c.first_name,
                    c.last_name,
                    c.company
                FROM interactions i
                JOIN customers c ON i.customer_id = c.id
                WHERE i.interaction_date >= datetime('now', '-' || ? || ' days')
                ORDER BY i.interaction_date DESC
            """
            results = db.execute_query(query, (days,))
            
            if not results:
                return [types.TextContent(type="text", text=f"📅 No interactions found in the last {days} days")]
                
            return [types.TextContent(type="text", text=f"📅 Recent Interactions (Last {days} days):\n\n{json.dumps(results, indent=2, default=str)}")]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"❌ Error retrieving recent interactions: {str(e)}")]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())