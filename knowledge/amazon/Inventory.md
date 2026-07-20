---
title: "Amazon Inventory Agent"
platform: "amazon"
agent: "inventory"
country: "india"
document_type: "knowledge_base"
topic: "Inventory Management"
version: "2026"
last_updated: "2026-07-19"
source: "NotebookLM + Amazon Seller Documentation"
---

 # **SellerOS Inventory Knowledge Base**

## **Inventory Management Overview**

Inventory management on Amazon.in is primarily conducted through the **Manage All Inventory** dashboard in Seller Central. This workspace provides essential tools for searching, viewing, and updating product listing and stock information. Sellers utilize this portal to maintain accurate stock levels, monitor sales performance, and identify issues that may impact product availability.

Effective inventory management involves several core activities:

* **Tracking:** Monitoring daily sales and current stock levels via the Inventory tab.
* **Updating:** Manually adjusting available quantities for merchant-fulfilled offers to prevent overselling.
* **Reporting:** Utilizing custom business reports and inventory ledger data to visualize stock movement.
* **Optimization:** Addressing inactive or suppressed listings to restore sales opportunities.

---

## **Fulfillment Models and Inventory Storage**

Amazon offers different fulfillment models that dictate where inventory is stored and how it is managed.

### **Fulfillment by Amazon (FBA)**

Under the FBA model, Amazon provides an all-in-one solution for inventory storage and logistics.

* **Storage:** Sellers ship their products to **Amazon Fulfillment Centers (FCs)**, which are advanced warehouses within Amazon's global network.
* **Inbounding:** Products are received at the FC, stored safely, and then picked, packed, and shipped upon receipt of a customer order.
* **Prime Eligibility:** Products stored in FBA are automatically eligible for the Prime badge and premium delivery options.
* **Returns:** Amazon manages customer support and the return of inventory to the fulfillment center.

### **Seller Flex**

Seller Flex is a hybrid model that allows sellers to achieve FBA-like benefits while maintaining inventory in their own premises.

* **Control:** Inbounding is performed by the seller's own manpower, which eliminates discrepancies related to missing or damaged units during transit to an Amazon FC.
* **Agility:** Refilling stock during low-inventory or out-of-stock scenarios is faster through the direct inbound feature.
* **Removal and Returns:** Removal orders and customer returns are processed immediately at the seller's location, allowing for faster disposal of damaged goods or restocking of sellable units.

### **Merchant-Fulfilled (Easy Ship and Self-Ship)**

* **Easy Ship:** The seller stores and packs inventory at their own location, while Amazon logistics handles the pickup and delivery.
* **Self-Ship:** The seller is entirely responsible for storing inventory and managing the end-to-end delivery process using third-party carriers.

---

## **Inventory Tracking and Reporting**

Accurate data visibility is critical for preventing stockouts and managing warehouse health.

### **The Inventory Ledger and Custom Reports**

The **Custom Report Builder** allows sellers to visualize specific aspects of their inventory by dragging and dropping relevant data fields.

* **Aggregated Data:** The Inventory business view aggregates information for specific FNSKU and Fulfillment Center combinations over a given date range.
* **Stock Statuses:** Reports track inventory that is in transit between warehouses, currently in a fulfillment center, being delivered to buyers, or identified as lost or damaged.
* **Reconciliation:** The Inventory business view is designed to match the **Inventory Ledger Report** for a consistent date, FNSKU, and FC ID combination.

### **Key Inventory Attributes**

Sellers can track inventory using the following reporting attributes:

* **Starting Warehouse Balance:** Units available in FCs at the beginning of a reporting period.
* **Ending Warehouse Balance:** Units available in FCs at the end of the reporting period.
* **Receipts:** Units received from inbound shipments to FCs.
* **Warehouse Transfer In/Out:** Total units transshipped between different FCs.
* **In Transit Between Warehouses:** Units currently moving within the Amazon fulfillment network.
* **Disposition:** The physical condition of inventory units, categorized as **Sellable** or **Damaged**.

---

## **Inventory Status and Maintenance**

Inventory health is monitored through status filters in the Manage Products dashboard.

### **Listing and Inventory Statuses**

* **Active:** Items that are currently live and available for customer purchase.
* **Inactive:** Listings that were previously live but are no longer buyable. Common causes include inventory depletion (out of stock), pricing errors, or policy concerns.
* **Stranded Inventory:** FBA inventory that is stored in a fulfillment center but does not have an active listing on Amazon, making it unavailable for sale.
* **Suppressed:** Listings hidden from search results due to quality issues, such as missing main images or title violations.

### **SKU and Offer Management**

* **Closing a Listing:** This action sets the status to Inactive but retains the SKU and all sales history/product information in the account. Listings can be reactivated at any time.
* **Deleting a Listing:** This permanently removes the SKU and all associated sales history and product data. After deletion, an SKU may not be available for reuse for up to 24 hours.
* **Quantity Updates:** For merchant-fulfilled items, quantity can be updated inline in the Quantity column of the Manage All Inventory page.

---

## **Common Inventory Issues**

### **Out of Stock**

- Running out of inventory reduces visibility and Buy Box eligibility.
- Frequent stockouts negatively affect customer experience and sales.

### **Stranded Inventory**

Common reasons include:

- Missing listing information.
- Listing removed or suppressed.
- Pricing errors.
- ASIN or SKU issues.

### **Suppressed Listings**

Listings may become suppressed due to:

- Missing product images.
- Incomplete attributes.
- Invalid titles.
- Policy violations.

### **Inventory Discrepancies**

Common causes include:

- Incorrect stock updates.
- Delayed inbound processing.
- Damaged inventory.
- Incorrect SKU assignment.

--- 

## **Removals, Damages, and Reconciliation**

When inventory is no longer sellable or needs to be returned to the seller, specific procedures must be followed.

### **Removal Orders**

* Sellers can request to have their inventory removed from an Amazon FC and returned to their designated address.
* Under certain promotions, FBA removal fees may be waived for a limited time or for a specific number of units.
* In the Seller Flex model, removal orders are processed instantly compared to the longer timelines of standard FBA.

### **Lost or Damaged Inventory**

* **Warehouse Lost/Damaged:** Units identified as lost or damaged while under Amazon's care in a fulfillment center.
* **Found Units:** Units previously reported as missing that have been located and returned to sellable inventory.
* **Reimbursement Claims:** Sellers may be eligible for reimbursement for units lost or damaged in an FC or during removal.
* **Standard Claim Windows:** Typically, claims for units missing from inbound shipments or warehouse damage must be filed within **60 days** of the event. Claims for lost removal shipments must be filed within **30 days** of the ship date.

### **Reconciliation Best Practices**

* Monitor the **Activity Table** in the Custom Report Builder to track the status of report generations (e.g., In Progress, Ready for download).
* Use the **Fix Your Products** tab to identify and resolve listings that are inactive due to inventory issues.
* *Note: Supplemental Knowledge — It is standard practice to perform weekly reconciliation by comparing "Inventory Receipts" in the Ledger against the "Shipping Queue" to ensure all shipped units were correctly checked into the FC.*

---

## **Inventory Policies and Best Practices**

### **Operational Standards**

* **Accuracy:** Maintain precise quantity counts for Merchant-Fulfilled Network (MFN) listings to avoid order cancellations.
* **Inbound Compliance:** When sending shipments to FBA, ensure that chosen FCs are added as an **Additional Place of Business (APOB)** in GST registration to remain tax-compliant.
* **Sorting:** Amazon uses standard display logic for child ASINs in variation families based on sales performance; sellers cannot request preferential sorting.

### **Performance and Growth (The STEP Program)**

The **Amazon STEP Program** is a performance-based benefit system that tracks metrics to help sellers grow.

* **Benefits:** Improving performance levels (from Basic to Premium) can unlock benefits such as weight handling fee waivers and faster disbursement cycles.
* **Metric Monitoring:** Sellers should use the **Sales Dashboard** and **Voice of the Customer** tool to identify product issues that lead to high return rates, which negatively impacts inventory health.

### **Inventory Best Practices**

- Monitor inventory daily.
- Replenish stock before inventory reaches critical levels.
- Review stranded inventory regularly.
- Fix suppressed listings immediately.
- Maintain accurate SKU and quantity records.
- Reconcile inventory reports periodically.
- Forecast demand during seasonal sales and promotions.

### **Common Mistakes to Avoid**

* **Ignoring Stranded Inventory:** Allowing units to sit in an FC without an active listing leads to unnecessary storage fees without the possibility of sales.
* **Late Reimbursement Claims:** Failing to file claims within the 30 or 60-day windows may result in the permanent loss of reimbursement eligibility.
* **Duplicate Listings:** Refrain from creating multiple detail pages for the same unique product, as this violates listing policies and complicates inventory tracking.

---
## **Troubleshooting**

### **Inventory Not Updating**

Possible causes:

- Feed processing delays.
- SKU mismatch.
- Incorrect inventory file.
- Pending listing status.

### **FBA Shipment Delays**

Possible causes:

- Shipment not checked in.
- Labeling errors.
- Missing shipment plan.
- Inventory still being received.

### **Inventory Not Available**

Check:

- Listing status.
- Inventory quantity.
- Pricing.
- Buy Box eligibility.
- Account health notifications.

---

## **Inventory Health Metrics**

Monitor the following regularly:

- In-Stock Rate
- Out-of-Stock Rate (OOS)
- Sellable Inventory
- Unsellable Inventory
- Stranded Inventory
- Inventory Turnover
- Excess Inventory
- FBA Storage Utilization

---