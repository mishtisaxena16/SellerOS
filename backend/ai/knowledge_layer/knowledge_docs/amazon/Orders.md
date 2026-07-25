---
title: "Amazon Orders Agent"
platform: "amazon"
agent: "orders"
country: "india"
document_type: "knowledge_base"
topic: "Order Management and Processing"
version: "2026"
last_updated: "2026-07-19"
source: "NotebookLM + Amazon Seller Documentation"
---

# **Amazon Order Management Knowledge Base**

This knowledge base explains how Amazon Seller Central manages customer orders throughout their complete lifecycle, including order creation, verification, fulfillment, shipment confirmation, cancellations, buyer communication, reporting, and operational performance metrics. Proper order management improves customer satisfaction, reduces cancellations, and helps maintain healthy seller performance metrics.

## **Order Management Overview**

The **Manage Orders** tool is the central dashboard in Seller Central used to view a list of all orders, access specific order details (product, buyer, and shipping information), and perform essential tasks such as printing packing slips and issuing refunds.

### **Order Search and Filtering**

To investigate specific orders, especially those older than 30 days, sellers should use the search feature on the Manage Orders page. Results can be filtered by:

* **Status** (Pending, Unshipped, Shipped, Cancelled).
* **Date range** (Seller Central supports viewing data for specific broad ranges through standard reports, while the Custom Report Builder initially supports 30-day snapshots).
* **Order ID**.

### **Common Order Processing Mistakes**

- Shipping Pending orders.
- Forgetting to confirm shipment.
- Missing Estimated Ship Dates.
- Ignoring cancellation notifications.
- Not checking Seller Central daily.
- Providing incorrect tracking information.

---

## **Order Statuses and Lifecycle**

The lifecycle of an order is defined by its status, which dictates the actions a seller can or must take.

### **1\. Pending Orders**

A status of **Pending** indicates that the order is being verified. Sellers **cannot** cancel or confirm an order while it is in this status.

* **Verification Timeline:** Payment and order detail verification can extend processing times for as long as 21 days.
* **Common Causes:**
 * Amazon has been unable to obtain authorization for the buyer's credit card.
 * For FBA orders, the buyer qualified for free shipping and the order is waiting for all items to be gathered.
 * For FBA orders, one item in a multiple-item order is out of stock.
 * For **Subscribe & Save** deliveries, orders are placed several days in advance to align with the customer's delivery schedule.
* **Operational Warning:** Never ship an order while it is in Pending status, even if the buyer contacts you directly.

### **2\. Unshipped Orders**

Once payment is verified, the status changes from Pending to **Unshipped**. This is the stage where fulfillment actions begin.

* **Verification Requirement:** Only ship orders that can be verified as Unshipped in Manage Orders.
* **Inventory Impact:** Inventory is updated to reflect the order as soon as it is placed, even while Pending.

### **3\. Shipped Orders**

Once an item is dispatched, the seller must confirm the shipment to transition the status to **Shipped**.

* **Shipping Confirmation:** Confirmation is mandatory to maintain an accurate late shipment rate and to trigger the charging of the buyer.

### **4\. Cancelled Orders**

Orders may be cancelled by the seller (if they cannot fulfill the item) or automatically by Amazon.

* **Auto-Cancellation (Standard):** If a shipment is not confirmed within 30 days of the order date, Amazon cancels the order automatically. The buyer will not be charged, even if the item was already shipped.
* **Easy Ship Auto-Cancellation:** Orders are cancelled after the estimated ship date \+ 1 day if they are not scheduled for pickup, or if the item is not handed over to the associate after scheduling.
* **Guaranteed Delivery Auto-Cancellation:** Orders are cancelled if not handed over to a pickup associate by the estimated ship date.

---

## **Order Processing Workflows**

### **Standard Fulfillment Tasks**

On the **Order Details** page, sellers can complete the following tasks:

* **Print Packing Slips:** Accessed via the button on the right-hand side of the Order Details page.
* **Manage Seller Order ID:** If a business uses an external automated invoicing system, sellers can include their own unique ID (up to 50 alphanumeric characters) by clicking "Edit" next to "Your Seller Order ID".
* **Issue Refunds:** Sellers can initiate full or partial refunds directly through the order management interface.

### **Automated Order Workflow**

The **Automated Order Workflow** is a self-service feature located on the "Contact Us" page. It allows sellers to resolve common queries without contacting support.

* **Use Cases:** Managing, scheduling, or rescheduling orders; cancelling pickups; handling damaged/wrong products; and finding buyer or payment information.
* **Procedure:** Sellers must click "Customers and Orders," specify the Order ID, and select the appropriate action (e.g., "Getting paid for an order") to see the top recommended solution.

### **Best Practices**

- Review new orders multiple times each day.
- Confirm shipments immediately after dispatch.
- Upload valid tracking information.
- Keep inventory synchronized to prevent overselling.
- Print packing slips for every shipment.
- Monitor Estimated Ship Dates carefully.

---

## **Order Reporting**

### **FBM (Fulfilled by Merchant) Order Reports**

The FBM Order Report is a tab-delimited text file containing buyer information necessary for fulfillment.

* **Data Included:** Product details, buyer information, and delivery calculation details (Handling time, Transit time).
* **Confidentiality:** Reports do **not** include the buyer’s billing address or credit card information.
* **Generation:** Reports can be generated manually for the past 1, 2, 7, 15, or 30 days. Recurring reports can also be scheduled.
* **Archiving:** Sellers are encouraged to archive reports daily as Seller Central does not generate reports for data older than 30 days.

### **Common Order Issues**

#### **Order remains in Pending status**

Possible reasons include:

- Payment authorization is pending.
- Buyer verification is incomplete.
- Inventory allocation is still in progress.

#### **Unable to ship an order**

Possible reasons include:

- Order is still Pending.
- Inventory unavailable.
- Shipping template restrictions.
- Pickup scheduling problems.

#### **Shipment confirmation failed**

Possible reasons include:

- Invalid tracking ID.
- Incorrect carrier selected.
- Order already cancelled.

---

## **Order Communication and Notifications**

### **"Sold, Ship Now" Notifications**

Amazon sends email notifications for every shippable order.

* **Best Practice:** Do not rely solely on email. Sellers should check Manage Orders or the Unshipped Orders report at least once a day.
* **Troubleshooting Missing Emails:**
 * **Blocked Connections:** Ensure the ISP is not filtering emails from Amazon.
 * **Bounced Emails:** Check if the inbox is full or the contact information in Seller Central is incorrect.
 * **Spam Filters:** Add `seller-notification@amazon.com` to the contacts list and check Junk/Trash folders.

### **Buyer-Seller Messaging Service**

This is the **only approved method** for communicating with buyers.

* **Permitted Use:** Contacting buyers to complete orders or respond to customer service questions.
* **Prohibited Use:** Marketing or promotional communications via email, physical mail, or telephone.

### **Seller Messaging Assistant (SMA)**

SMA is an automated conversational assistant that resolves common buyer inquiries.

* **Post-Order Enquiries:** SMA handles "Where is my stuff?", cancellations, returns, and invoice requests.
* **Benefit:** Reduces seller contact volume by resolving repeatable inquiries automatically.

### **Communication Best Practices**

- Respond to buyer messages promptly.
- Use only Buyer-Seller Messaging.
- Never send promotional messages.
- Keep communication professional and order-related.
- Retain records of important conversations.

---

## **Performance Metrics and Policies**

### **Key Performance Indicators (KPIs)**

Sellers must monitor metrics on the Seller Central dashboard to ensure policy compliance:

* **Total Cancellation Rate:** The percentage of orders cancelled by the seller.
* **Total Late Dispatch Rate:** The percentage of orders for which shipment confirmation is completed after the expected ship date.
* **A-to-z Guarantee Claims:** Buyers can file claims if they do not receive an order, typically starting 3 days after the maximum estimated delivery date or 30 days after the order date.

### **Why These Metrics Matter**

Amazon continuously evaluates seller performance using operational metrics. Poor performance can reduce Buy Box eligibility, affect account health, suspend shipping programs, or lead to account deactivation. Monitoring these metrics regularly helps maintain a healthy seller account.

### **Best Practices for Order Handling**

* **Overselling Prevention:** If a single item is accidentally sold to two buyers due to inventory lag, cancel the second order immediately and refund the buyer.
* **Tracking:** Use tracking for all shipments to reduce costs associated with lost items and protect against A-to-z claims.
* **Non-Receipt Claims:** If a buyer claims non-receipt, sellers should first ask the buyer to wait slightly longer, contact the shipping carrier, or check for a lost shipment before issuing a refund.
* **SAFE-T Claims:** Sellers can file a SAFE-T claim to appeal Amazon's decision to refund a customer if they believe they were not at fault.

## **Daily Order Management Checklist**

Every business day, sellers should:

- Check new orders.
- Verify Pending orders.
- Process Unshipped orders.
- Confirm dispatched shipments.
- Upload tracking numbers.
- Respond to buyer messages.
- Monitor cancellations.
- Review performance metrics.
- Archive order reports when required.

> **Important**
>
> Never dispatch an order until its status changes from Pending to Unshipped. Shipping orders before payment verification or failing to confirm shipments within the required timeframes can negatively impact account health, increase cancellation rates, and result in customer disputes.