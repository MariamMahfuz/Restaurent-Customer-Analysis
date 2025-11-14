import matplotlib.pyplot as plt
import pyodbc
import pandas as pd
import matplotlib.pyplot as mpl
from unicodedata import category

#print(pyodbc.drivers())
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=DESKTOP-99N3O9C;"
    "DATABASE=RestaurentDB;"
    "Trusted_Connection=yes;"

)
cursor= conn.cursor()

#Create a new database
cursor.execute('''IF NOT EXISTS (SELECT 1 FROM sys.schemas where name = N'App')
    EXEC('CREATE SCHEMA app AUTHORIZATION dbo;');   
    IF OBJECT_ID(N'app.Customers', N'U') IS NULL
    BEGIN
    CREATE TABLE app.Customers (
    CUSTOMERID INT IDENTITY(1,1) PRIMARY KEY,
    FULLNAME NVARCHAR(100) NOT NULL,
    PHONE VARCHAR(10) NULL,
    EMAIL VARCHAR(20) NULL,
    CREATEDat DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    )
    END
    
''')
cursor.commit()

#Create MenuItems Table----------------------------------
cursor.execute('''
IF Object_ID(N'app.MenuItems', N'U') IS NULL  
BEGIN
CREATE TABLE app.MenuItems(
ItemID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
ItemName NVARCHAR(100),
Category VARCHAR(50),
PRICE DECIMAL(6,2)
);
END
''')
cursor.commit()

#Create ORDER Table-----------------------------------
cursor.execute('''
 IF object_ID('app.Orders', N'U') is NULL
BEGIN
CREATE TABLE app.Orders(
OrderID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
CustomerID INT,
ItemID INT,
Quantity INT,
OrderDate DATE,
FOREIGN KEY (CustomerID) REFERENCES app.Customers(CUSTOMERID),
FOREIGN KEY (ItemID) REFERENCES app.MenuItems(ItemID)

);
END

''')



#Insert Values in Customer Table--------------------------------
rows_customers=[
('Mahfuz', '1234767890', 'mariam@example.com'),
('Nila', '1234767890', 'mariam@example.com')
]
# cursor.executemany(
#     '''
#     INSERT INTO app.Customers (FULLNAME, PHONE, EMAIL)
#     VALUES (?, ?, ?)
#     ''',
#     rows_customers
#     )

cursor.commit()


#insert values to MenuItems------------------------
rows_items=[
    ('Rice', 'Asian', 25),
    ('Shrimp', 'Japanese', 26),
    ('Sushi', 'Japanese', 30),
    ('Rice', 'Asian', 25),
    ('Rice', 'Asian', 25),
    ('Rice', 'Asian', 25)

]
# cursor.executemany('''
# INSERT INTO App.MenuItems( ItemName, Category, Price)
# VALUES (?,?,?)
# ''',
# rows_items
# )
# cursor.commit()
#

#-----Insert Values-----------------------------------------------------------------
rows_orders=[
    # (4,1,25),
    # (5,2,35),
    # (6,3,45),
]
# cursor.executemany('''
# INSERT INTO App.Orders( CustomerID, ItemID, Quantity)
# VALUES (?,?,?)
# ''',

# rows_orders
# )
# cursor.commit()

query= " Select * from app.Orders ORDER BY OrderDate DESC"
df= pd.read_sql(query, conn)
print(df.head(5))


cursor.execute('''
Update app.Orders set OrderDate = CAST(GETDATE() AS DATE)''')
cursor.commit()


cursor.execute("USE RESTAURENTDB")
query_totalspent= (""" 
        SELECT c.FULLNAME, SUM(m.Price*o.Quantity) AS totalspent FROM app.ORDERS o
JOIN app.menuItems m ON m.ItemID = o.ItemID
JOIN app.Customers c ON c.CUSTOMERID= o.CustomerID
GROUP BY c.FULLNAME;
""" )
df_totalspent= pd.read_sql(query_totalspent, conn)
print(df_totalspent.head(5))


above_averagespent= ("""
SELECT 
    c.FULLNAME,
    SUM(m.Price * o.Quantity) AS Total_Purchase
FROM app.Orders AS o
JOIN app.MenuItems AS m ON m.ItemID = o.ItemID
JOIN app.Customers AS c ON c.CustomerID = o.CustomerID
GROUP BY c.FullName
HAVING SUM(m.Price * o.Quantity) > (
    SELECT 
        AVG(CustomerTotal)
    FROM (
        SELECT 
            SUM(menu.Price * ord.Quantity) AS CustomerTotal
        FROM app.Orders AS ord
        JOIN app.MenuItems AS menu ON menu.ItemID = ord.ItemID
        JOIN app.Customers AS cust ON cust.CustomerID = ord.CustomerID
        GROUP BY cust.CustomerID
    ) AS SubTotals
);

""")

above_average_df= pd.read_sql(above_averagespent, conn)
print(above_average_df.head(5))


popular_items= (""" SELECT TOP 1 m.ItemName AS PopularItem, O.quantity FROM app.menuitems AS m
Join app.Orders O ON o.ItemID= m.Itemid
Group By m.ITEMNAME, o.Quantity
Order BY o.Quantity DESC""")
popular_items_df= pd.read_sql(popular_items, conn)
print(popular_items_df.head(5))

print(popular_items_df.describe())
df_totalspent_sorted =df_totalspent.sort_values(by='totalspent', ascending=False)
print(df_totalspent_sorted.head(5))


#visualization to matplotlib
# plt.bar(df_totalspent['FULLNAME'], df_totalspent['totalspent'])
# plt.title("Total Spending by Customer")
# plt.xlabel("Customer")
# plt.ylabel("Total Spent")
# plt.show()

print(df_totalspent.head(5))
print(above_average_df.head(5))

#--MERGING TABLE
merged_df = df_totalspent.merge(above_average_df, on='FULLNAME', how='left')
print(merged_df)


#melt two columns and visualize it
Melted_merge= pd.melt(merged_df, id_vars='FULLNAME', value_vars=['totalspent', 'Total_Purchase'], var_name='spend and amount Category', value_name='Value' )
print(Melted_merge)

#visualize this melted data
import seaborn as sns
sns.barplot(
    data=Melted_merge,
    x='FULLNAME',
    y= 'Value',
    hue='spend and amount Category'
)

plt.title("Melted data in quantity and spent amount")
plt.ylabel('Amount')
plt.xlabel('Customer_Name')
plt.show()
# with pd.ExcelWriter('Restaurant_Sales_Report.xlsx') as writer:
#     df_totalspent.to_excel(writer, sheet_name='TotalSpent', index=False)
#     above_average_df.to_excel(writer, sheet_name='AboveAvg', index=False)
#     popular_items_df.to_excel(writer, sheet_name='PopularItem', index=False)
