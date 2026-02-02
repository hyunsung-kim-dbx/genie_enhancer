
Unity Catalog metric views
Metric views provide a centralized way to define and manage consistent, reusable, and governed core business metrics. This page explains metric views, how to define them, control access, and query them in downstream tools.

What is a metric view?
Metric views abstract complex business logic into a centralized definition, enabling organizations to define key performance indicators once and use them consistently across reporting tools like dashboards, Genie spaces, and alerts. Metric views are defined in YAML format and registered in Unity Catalog. You can create them using SQL or the Catalog Explorer UI. Like any other table or view, metric views can be queried using SQL.

Diagram showing that metric views are defined on source tables, views, and queries and consumed from code and no code interfaces.

Why use metric views
Unlike standard views that lock in aggregations and dimensions at creation time, metric views separate measure definitions from dimension groupings. This allows you to define metrics once and query them flexibly across any dimension at runtime, while the query engine automatically generates the correct computation.

Metric views provide key benefits:

Standardize metric definitions across teams and tools to prevent inconsistencies.
Handle complex measures like ratios and distinct counts that cannot be safely re-aggregated in standard views.
Enable flexible analysis by supporting star and snowflake schemas with multi-level joins (for example, orders → products → categories).
Accelerate query performance with built-in materialization that automatically pre-computes and incrementally updates aggregations.
Simplify the user experience while maintaining SQL transparency and governance.
Example
Suppose you want to analyze revenue per distinct customer across different geographic levels. With a standard view, you would need to create separate views for each grouping (state, region, country) or compute all combinations in advance using GROUP BY CUBE() and filter afterward. These workarounds increase complexity and lead to performance and governance issues.

With a metric view, you define the metric once (sum of revenue divided by distinct customer count), and users can group by any available geography dimension. The query engine rewrites the query behind the scenes to perform the correct computation, regardless of how the data is grouped.

Components
A metric view specifies a set of metric definitions, which include dimensions and measures, based on a data source, or multiple sources if join logic is used. The source in the metric view definition can be a view, table, or SQL query. Joins are only supported on views and tables.

A dimension is a categorical attribute that organizes and filters data, such as product names, customer types, or regions. Dimensions provide the labels and groupings needed to analyze measures effectively.

A measure is a value that summarizes business activity, typically using an aggregate function such as SUM() or AVG(). Measures can be applied to one or more base fields in the source table or view, or reference earlier-defined dimensions and measures. Measures are defined independently of dimensions, allowing users to aggregate them across any dimension at runtime. For example, defining a total_revenue measure enables aggregation by customer, supplier, or region. Measures are commonly used as KPIs in reports and dashboards.

Access and edit metric views
Metric views are registered to Unity Catalog. Users with at least SELECT permission on the metric view can access details using the Catalog Explorer UI.

View details in the Catalog Explorer UI
To view the metric view in Catalog Explorer:

Click Data icon. Catalog in the sidebar.
Browse available data or use the search bar to search for the metric view by name.
Click the name of the metric view.
Use the tabs to view information about the metric view:
Overview: Shows all measures and dimensions defined in the metric and any semantic metadata that has been defined.
Details: Shows the complete YAML definition for the metric view.
Permissions: Shows all principals who can access the metric view, their privileges, and the containing database object on which the privilege is defined.
Lineage: Displays related assets, such as tables, notebooks, dashboards, and other metric views.
Insights: Queries made on the metric view and users who accessed the metric view in the past 30 days are listed in order of frequency, with the most frequent on top.
Enable collaborative editing
By default, only the owner of a metric view can edit its definition. To enable multiple people to collaborate on the same metric view, transfer ownership to a group. All members of that group can then edit the definition, but only access data the group has permissions to see.

To enable collaborative editing:

Create or identify a group that should have edit access to the metric view. See Groups.
Grant the group SELECT access to all tables the metric view depends on.
Transfer ownership of the metric view to the group. See Transfer ownership.
Add or remove users from the group to control who can edit the metric view.
Query a metric view
You can query metric views in the same way as a standard view. Run queries from any SQL editor that is attached to a SQL warehouse or other compute resource running a supported runtime.

Query measures and dimensions
All measure evaluations in a metric view query must use the MEASURE aggregate function. For complete details and syntax, see measure aggregate function.

note
Metric views don't support SELECT * queries. Measures are aggregations that must be explicitly referenced by name using the MEASURE() function, so you must specify the dimensions and measures you want to query.

JOINs at query time aren't supported. To join tables:

Define JOINs in the YAML specification that creates the metric view. See Use joins in metric views.
Use common table expressions (CTEs) to join sources when querying a metric view. See Common table expression (CTE).
View details as a query result
The following query returns the full YAML definition for a metric view, including measures, dimensions, joins, and semantic metadata. The AS JSON parameter is optional. For complete syntax details, see JSON formatted output.

SQL
DESCRIBE TABLE EXTENDED <catalog.schema.metric_view_name> AS JSON

The complete YAML definition is shown in the View Text field in the results. Each column contains a metadata field that holds semantic metadata.

Consume metric views
You can also use metric views throughout the Databricks workspace. For more information, see the associated documentation:

Use metric views with AI/BI dashboards
Use metric views with AI/BI Genie
Set alerts on metric views
Troubleshoot with query profile
Work with metric view metadata using the Databricks JDBC Driver
Limitations
The following limitations apply to metric views:

Metric views do not support Delta Sharing or data profiling.
Next steps
Create a metric view
Use semantic metadata in metric views
Use joins in metric views
Use window measures in metric views
Materialization for metric views