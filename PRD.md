## **Revised MVP Outline for The Sweet Escape**

### **Overview**
**Objective:**  
Develop a lightweight, visually appealing (think “pink dashboard”) MVP that enables Sam (the owner) of The Sweet Escape to manually manage orders on a calendar-based interface. The system will then automatically trigger review request messages (via email or WhatsApp) a day or two after the scheduled delivery or collection date.

### **Key Differences from the Original Plan**
- **No POS Integration:**  
  Since The Sweet Escape doesn’t use a POS, Sam will manually enter order details.
- **Custom Dashboard:**  
  A simple, beautiful pink dashboard with a calendar view will be created. This interface is designed to be extremely user-friendly for non-tech-savvy users.
- **Communication Channel Selection:**  
  For each order, Sam can tick a box to choose whether the customer receives a review request via email or WhatsApp.
- **Order Trigger Timing:**  
  The system sends out review requests a day or two after the order’s delivery/collection date (this can be configurable if needed).

---

## **Revised PRD Addendum for The Sweet Escape MVP**

### **1. User Flow**

1. **Dashboard Login & Order Management:**  
   - **Login:** Sam logs in using a simple, secure interface.
   - **Dashboard Overview:** The main screen shows a calendar view with upcoming orders. The design will use a pleasant pink theme.
   - **Order Entry:**  
     - Sam clicks “Add Order” and is presented with a form.
     - **Required Fields:**  
       - Order Number/ID  
       - Customer Name and Contact Information  
       - Delivery or Collection Date (via calendar picker)  
       - Communication Preference: Checkbox/toggle to select between Email or WhatsApp  
     - Sam submits the order details.
   - **Calendar View:**  
     - Newly entered orders appear on the calendar, color-coded for delivery vs. collection if desired.

2. **Automated Review Request Trigger:**  
   - **Timing:**  
     - The system monitors the calendar. A scheduled job runs daily to check for orders that reached their delivery/collection date one or two days ago.
   - **Message Dispatch:**  
     - Based on the communication channel chosen (email or WhatsApp), the system sends out a pre-built review request message to the customer.
     - The message will invite the customer to rate their experience, and if a 5-star rating is provided, they are redirected to leave a public review (e.g., Google My Business). For any rating below 5, the customer is directed to a feedback form that goes privately to Sam.

3. **Follow-Up & Reporting:**  
   - Sam can view a simple report in the dashboard summarizing:
     - Total orders processed
     - Number of review requests sent
     - Outcomes: How many resulted in 5-star reviews and how many flagged lower ratings for private follow-up.

### **2. Functional Requirements**

#### **A. Dashboard & Order Management**
- **Design & Branding:**  
  - A visually appealing pink-themed UI, optimized for simplicity.
- **Calendar Integration:**  
  - Display orders in a monthly/weekly calendar view.
  - Allow filtering (e.g., by delivery vs. collection).
- **Order Form:**  
  - Simple form for manual order entry.
  - Fields: Order ID, Customer Name, Contact Details, Date, Communication channel selection (email/WhatsApp).
- **Order Editing/Deletion:**  
  - Options for Sam to edit or delete orders if needed.

#### **B. Automated Communication**
- **Scheduling Engine:**  
  - A background job or cron task that runs daily, checking for orders with a delivery/collection date of “yesterday” or “the day before yesterday” (configurable).
- **Messaging Integration:**  
  - Integrate with an email provider (like SendGrid or Mailchimp) for email messages.
  - Integrate with WhatsApp Business API for WhatsApp messaging.
- **Message Templates:**  
  - Pre-built templates that include a friendly prompt to leave a review.
  - If 5 stars are given, redirect customers to a public review site.
  - For lower ratings, redirect customers to a private feedback form that sends details to Sam.

#### **C. Reporting & Notifications**
- **Dashboard Metrics:**  
  - Basic reporting on sent review requests, responses, and flags for lower ratings.
- **Alert System:**  
  - Optional: Provide Sam with a simple notification if any feedback is flagged for private follow-up.

### **3. Non-Functional Requirements**

- **Usability:**  
  - The interface must be intuitive, with minimal steps for order entry.
- **Reliability:**  
  - The automated review trigger should run consistently once scheduled.
- **Scalability:**  
  - While initially for a single tester environment, ensure that the architecture is modular for future expansion.
- **Security:**  
  - Ensure secure login and data storage (encryption in transit and at rest).

### **4. Technical Architecture (High-Level)**
- **Frontend:**  
  - A simple web app (HTML/CSS/JavaScript with a framework like React or Vue for the calendar view) styled with a pink-themed design.
- **Backend:**  
  - A lightweight server (using Node.js, Python, or similar) that handles:
    - Order management APIs.
    - Scheduling logic for dispatching messages.
    - Integration endpoints for email and WhatsApp messaging.
- **Database:**  
  - A simple relational database (e.g., PostgreSQL or MySQL) to store order data and logs.
- **Integrations:**  
  - **Email:** SendGrid/Mailchimp API.
  - **WhatsApp:** WhatsApp Business API.
  - **Scheduling:** Use cron jobs or a task scheduler service (like Celery with Python or similar in Node.js).

---

## **3. Next Steps for MVP Implementation**

1. **Design Phase:**  
   - Create wireframes/mockups for the pink-themed dashboard, focusing on the calendar view and order entry form.
   - Validate designs with Sam for usability and aesthetic appeal.

2. **Development Phase:**  
   - Set up the backend server and database.
   - Develop the order management module (CRUD operations for orders).
   - Implement the calendar interface and integrate it with backend APIs.
   - Build the automated messaging engine with the selected providers (email and WhatsApp).
   - Develop the logic for scheduling review requests based on order dates.

3. **Testing Phase:**  
   - Run initial tests with manual order entries to ensure the system triggers the correct messages.
   - Validate that the message routing (5-star vs. below 5) works as intended.
   - Ensure the dashboard reports accurately reflect order and message statuses.

4. **Pilot Rollout:**  
   - Launch the MVP with The Sweet Escape as the test environment.
   - Collect feedback from Sam on ease-of-use and system performance.
   - Iterate based on feedback before a broader rollout.
