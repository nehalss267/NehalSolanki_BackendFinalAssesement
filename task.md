
HubSpot DLT Integration Test-Task List
OvervieM
Complete test to validatethe DLT Generator tool by implementing a HubSpot Deals data
extraction service.
Important: The workilow starts with generating the service structure first, then updating the
documentation templates provided in the dlocs/folder.
Phase 1: Generate Structure & Update Documentation
Timeline: Days 1-2
Task 1.1: Generate Service Structure
Day 1 (Morning-2 hours) What you need to do:
Clone the repository: git clone https://github.com/Glynac-Al/Backend-Tools-and-assessment.git 
Croate configuration JSON file with project name "hubspot-deals-otl"
Set service name to "hubspot_deals"
Configure ports: dev-5200, stage-5201, prod-5202
Run the DLT generatar: python dit_generator.py
Navigate to generated project directory
cyour-config.json
Explore the generated docs/folder to see available documentation templates
Task 1.2: Update Hub5pot Deals API Integration Document
Day 1 (Aftermoon-3 hours) What you need to do:
Open the API integration documentation template in the generated docs/ folder
Update with HubSpot CRM API v3 for deals endpoint details
Document authentication method (private app access tokens)

Configure ports: dev=5200, stage=5201, prod=5202
Run the DLT generator: python dlt_generator.py -c your-config.son
Navigate to generated project directary
Explore the generated docs/folder to see avallable documentation templates

Task 1.2: Update HubSpot Deals API Integration Document
Day 1 (Afternoon-3 hours) What you need to do:
Opon the API integration documentation tomplate in the generated docs/ folder
Update with HubSpot CRM API v3 for deals endpoint details
Document authentication method (private app access tokens)
Document the deals endpoint structure: /crm/v3/objects/deals
Document query parameters: limit, after, properties, archived
Document response structure with sample 1SON
Document rate limitsand error handling
List all available deal properties from Hubspot docs

Task 1.3: Update Database Schema Document
Day 2 (Morning-2 hours) What you need to do:
Open the database schema template in the generated docs/folder

Configure ports: dev=5200, stage=5201, prod=5202
Run the DLT generator: python dlt_generator.py -c your-config.son
Navigate to generated project directary
Explore the generated docs/folder to see avallable documentation templates

Task 1.2: Update HubSpot Deals API Integration Document
Day 1 (Afternoon-3 hours) What you need to do:
Opon the API integration documentation tomplate in the generated docs/ folder
Update with HubSpot CRM API v3 for deals endpoint details
Document authentication method (private app access tokens)
Document the deals endpoint structure: /crm/v3/objects/deals
Document query parameters: limit, after, properties, archived
Document response structure with sample 1SON
Document rate limitsand error handling
List all available deal properties from Hubspot docs



Task 1.3: Update Database Schema Document
Day 2 (Morning-2 hours) What you need to do:
Open the database schema template in the generated docs/folder
Design PostgreSQL table structure for deals dat
Map HubSpot property types to PostgreSQL types
Include ETL metadata felds (extracted at, scan id, tenant id)
Design indexes for performance (tenant, dates, stages)
Document the schema with CREATE TABLE statements
Plan for multi-tenant data isolation

Task 1.4: Update API Documentation
Day 2 (Afternoon-2 hours) What you need to do:
Open the API docume template in the generated docs/folder
Update with the REST endpoints your service will expose
Document request/response schemas for deal extraction
authentication requirements
Document error responses and status codes
Create example requests for starting scans and getting results

Phase 2: Data Addition Tasks
Timeline: Days 3-4

Task 2.1: Set Up Hub5pot Developer Account
Day 3 (Full day- 4 hours) What you need to do:
Go to https://developers.hubspot.com/
Create a free developer account
Create a test account within the developer portal
Navigate to Settings→ Integrations Private Apps
Create a new private app called "DLT Deals Extractor
Configure the required scopes: crm.objects.deals.read
Generate and save the access token securely

Task 2.2: Add Test Deal Records
Day 4 (Fuil day-3 hours) What you need to do:
Create 5 different test deals in your HubSpot test account
Include variety in deal stages, amounts, and types
different deal stages: qualified, presentation scheduled, closed won, closed lost
Include deals with different amounts: $5K, $25K, $50K, $75K, $100K
Add meaningful descriptions and close dates
deal IDs for verification later

Phase 3: Implementation Tasks
Timeline: Days 5-7
Task 3.1: Update Environment Configuration
Day 5 (Morning -1 hour) What you need to do:
Update the generated.enw file with HubSpot-specific settines
Configure HubSpot API base URL and timeout settings
Set pipeline name and database schema for hubspot deals
Keep database credentials for development environment


Task 3.2: Implement Hubspot API Service

Day 5 (Afternoon) - Day 6 (Morning-6 hours total) What you need to do:
Page 3 of 1,650 words: Editor Suggestom Smaо
Create services/hulbspot api service.py file
Implement authentication method using HubSpot access tokens
Implement get deals() method with pagination support
Add rate limiting handling [Hub5pot: 150 requests/10 seconds)
Add error handling for common Hubspot API errors
Implement credential validation method
Add logging throughout the service

Task 3.3: Implement Data Source
Day 6 (Aftemoon) - Day 7 (Morning-6 hours total) What you need to do:
Update services/data_source.py with HubSpot deals extraction logic
Create DLT resource for deals with proper primary key
Implement pagination using HubSpot's cursor-based system
Add checkpoint suppart every N pages
Transform HubSpot deal properties to match your database schema
Handle data type conversions (dates, amounts, etc.)
adata to ecoro
Update services/extraction_service.py imports

Task 3.4: Test and Validate
Day 7 (Aftemoon-4 hours) What you need to do:
Start the Docker services: docker-compose up-d-build
Test health endpoint: curi http://localhost:5200/health
Create test extraction request with your HubSpot access token
Starta scan and monitor the status
Verify all 5 test deals are extracted correctly
Check database records match expected format

Test checkpoint functionality by interrupting and resuming
Verify API documentation at /docs/endpoint

Deliverables Checklist
Final Deliverable: Complete GitHub repository with working Hubspot Deals integration
Repository Deliverables Checklist:
Phase 1 Documentation:
[Generated service structure using DLT Generator
[] Updated HubSpot API integration document (docs/api-integratton.md)
[]Updated database schema design docurnent (docs/database-schema.md)
[]Updated service API documentation (docs/api-documentation.md)
Phase 2 Data Setup:
[]HubSpot developer account credentials documented
[)5 test deals created with IDs recarded in test-results/
[]Access token generated and secured (not committed to repo)
Phase 3 Implementation:
[]Updated environment configuration (env.example)
[]Implemented Hubspot API service (services/hubspot_api_service.py)
[]Implemented deals data source (services/data source.py)
[] Updated extraction service imports
Passing health checks documented
[]Successful extraction of test data proven



[]Passing health checks documented
[Successtul extraction of test data proven
[]Database verification results included
[]Working API documentation accessible
Repository Quality Requirements:
Clear README.md with setup instructions
[]All sensitive credentials in.env.example format
Test results and logs included in test-results/
[] Code is properly commented and formatted
[Docker services start without errors
[] All 5 test deals successfully extracted and documented

Success Criteria
DLT Generator creates complete service structure
Documentation templates are present in docs/folder and customizable
All 5 test deals estracted surepschullu


Phase 1: Documentation (20 Points)
Task 1.2: API Integration Documentation (7 Points)
[]7 pts: Complete Hubspot API documentation with all endpoints, auth, and examples
[15 pts: Good documentation with minar gaps in details
[]3 pts: Basic documentation covering main requirements
[]1 pt: Incomplete or undear documentation
[]0 pts: No docurmentation update or major errors
Task 1.3: Database Schema Documentation (7 Points]
[]7 pts: Complete schema with proper types, Indexes, and multi-tenant design
[]5 pts: Good schema with minor missing elements
3 pts: Basic scherma covering main requirements
[]1 pt: Incomplete schema or design Issues
[]0 pts: No schema documentation or major errors
Task 1.4: API Documentation (6 Points)
6 pts: Complete service AP! docs with request/response examples
[]4 pts: Good API documentation with minor gaps
[]2 pts: Basic API documentation
[0pts: No API documentation or major errors
Phase 2: Data Setup (20 Points)
Task 2.1: HubSpot Account Setup (10 Points)
[]10 pts: Complete setup with valld access token and proper scopes
[]7 pts: Setup.complete with minor configuration issues

Task 2.2: Test Data Creation (10 Points]
[]10 pts: All 5 test deals created with variety in stages, amounts, and data
[17 pts: 4-5 deals created with good variety
[]4 pts: 3-4 deals created with basic variety
[]2 pts: 1-2 deals created
[10 pts: No test deals created

Phase 3: Implementation (55 Points)
Task 3.1: Environment Configuration (5 Points)
[15 pts: Complete configuration with all HubSpot settings properly configured
[13 pts: Configuration mostly complete with minor issu
[]1 pt: Basic.configuration with several missing elements
[10 pts: Contiguration incomplete or incorrect
Task 3.2: HubSpot API Service Implementation (20 Points
[]20 pts: Coamplate implementation with auth, pagination, rate limiting, and orror
handling
[]15 pts: Good implementation with minor missing features

[]20 pts: Complete DLT data source with checkpointing, transformation, and proper
data handling
[]15 pts: Good implementation with minor issues
[10 pts: Basic implementation that extracts data successfully
[]5 pts: Partial Implementation with significant Issues
[]0 pts: Implementation fails or not completed

Task 3.4: Testing and Validation (10 Points)
[]10 pts: All tests pass, 5/5 deals extracted, health checks work, API docs accessible
[]7 pts: Most tests pass, 4-5 deals oxtracted wi
[]4 pts: Basic functionality works, 3-4 deals extracted
[]2 pts: Umited functionality, 1-2 deals extracted
[10 pts: Tosts fail or no successful data extraction

Scoring Thresholds
Excellent (90-100 points): Tool demonstrates producbion-ready capability with comprehensive
documentation and flawless implementation.
Good (75-89 points): Tool works well with minor gaps. Ready for production with some
additional work.
Satistartoru I60-78 nnintsh Rasiefunetionalitv nowen hut renuires cionifieant imornvemants

[]2 pts: Limited functionality, 1-2 deals extracted
[10 pts: Tests fail or no successful data extraction
Scoring Thresholds
Excellent (90-100 points): Tool demonstrates production-ready capability with comprehensive
documentation and flawless implementation.
Good (75-89 points): Tool works well with minor gaps. Ready for production with soms
additional work.
Satisfactory (60-74 points): Basic functionality proven but requires significant improvements
for production use.
Needs Improvement [40-59 points]: Tool shows promise but has major gaps that prevent
practical use
Unsatisfactory (0-39 points): Tool fails to demonstrate basic functionality or value proposition.
Success Criteria
Minimum Passing Score: 60 points
roduction Ready Score: 90+ polnts
5 test deals must be successfully extracted (automatic failure if 0 deals extracted)
Service must start without errors (automatic 10 point deduction if Docker fails)
