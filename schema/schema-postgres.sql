--
-- PostgreSQL database dump for the cloth and accessories retail website
--

-- Postgres database version - 15.3

--
-- Name: accounts_account; Type: TABLE;
-- This table contains details about all accounts in the retail website - both retail managers as well as the customers
--

CREATE TABLE accounts_account (
    id integer NOT NULL, -- primary key of the table accounts_account table
    password character varying(128) NOT NULL,
    first_name character varying(50) NOT NULL,
    last_name character varying(50) NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    phone_number character varying(50) NOT NULL,
    date_joined timestamp with time zone NOT NULL,
    last_login timestamp with time zone NOT NULL,
    role character varying(10) NOT NULL -- role can either be "Customer" or "Manager"
);

--
-- Name: category_category; Type: TABLE;
-- This table contains information about the product categories. 
-- Existing category_names: Dress, Pants, Jacket, Jeans, Shoes and Shirts
--

CREATE TABLE category_category (
    id integer NOT NULL, -- primary key of the table category_category
    category_name character varying(100) NOT NULL -- possible values: Dress, Pants, Jacket, Jeans, Shoes, Shirts
);

--
-- Name: orders_order; Type: TABLE;
-- Contains details about the orders placed by the customers 
--

CREATE TABLE orders_order (
    id integer NOT NULL, -- primary key of the table orders_order
    order_number character varying(20) NOT NULL,
    first_name character varying(50) NOT NULL,
    last_name character varying(50) NOT NULL,
    phone character varying(15) NOT NULL,
    email character varying(50) NOT NULL,
    address_line_1 character varying(50) NOT NULL,
    address_line_2 character varying(50) NOT NULL,
    country character varying(50) NOT NULL,
    state character varying(50) NOT NULL,
    city character varying(50) NOT NULL,
    order_note character varying(100) NOT NULL,
    order_total double precision NOT NULL,
    tax double precision NOT NULL,
    status character varying(10) NOT NULL,
    is_ordered boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    payment_id integer, 
    user_id integer -- foreign key of accounts_account.id
);

--
-- Name: orders_orderproduct; Type: TABLE; 
-- This table contains the details about products that have been ordered by the customers
--

CREATE TABLE orders_orderproduct (
    id integer NOT NULL, -- primary key of the table orders_orderproduct
    quantity integer NOT NULL,
    product_price double precision NOT NULL,
    ordered boolean NOT NULL,
    order_id integer NOT NULL, -- foreign key of orders_order.id
    payment_id integer, -- foreign key of orders_order.payment_id
    product_id integer NOT NULL, -- foreign key of store_product.id
    user_id integer NOT NULL -- foreign key of accounts_account.id
);

--
-- Name: orders_orderproduct_variations; Type: TABLE; 
-- This table contains information about the variations of the products ordered. 
-- There are two types of product variation: color and size
--

CREATE TABLE orders_orderproduct_variations (
    id integer NOT NULL, -- primary key of the table orders_orderproduct_variations
    orderproduct_id integer NOT NULL, -- foreign key of orders_orderproduct.id
    variation_id integer NOT NULL -- foreign key of store_variation.id
);

--
-- Name: orders_payment; Type: TABLE; 
-- This table contains just the payment details for an order 
--

CREATE TABLE orders_payment (
    id integer NOT NULL, -- primary key of the table orders_payment
    payment_id character varying(100) NOT NULL, -- foreign key of orders_order.payment_id
    payment_method character varying(100) NOT NULL,
    amount_paid character varying(100) NOT NULL,
    status character varying(100) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    user_id integer NOT NULL -- foreign key of accounts_account.id
);

--
-- Name: store_product; Type: TABLE;
-- This table contains details about the products we sell in our retail website
--

CREATE TABLE store_product (
    id integer NOT NULL, -- primary key of the table store_product
    product_name character varying(200) NOT NULL,
    product_brand character varying(200) NOT NULL,
    description text NOT NULL,
    price integer NOT NULL, -- price is in US dollars
    images character varying(100) NOT NULL,
    stock integer NOT NULL, -- stock column specifies how many of this product are in stock. 0 would mean the product is out of stock. 
    created_date timestamp with time zone NOT NULL,
    category_id integer NOT NULL -- foreign key of the category_category.id
);

--
-- Name: store_reviewrating; Type: TABLE; Schema: public; Owner: retailsdbuser
--

CREATE TABLE store_reviewrating (
    id integer NOT NULL, -- primary key of the table store_reviewrating
    subject character varying(100) NOT NULL,
    review text NOT NULL,
    rating double precision NOT NULL,
    status boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    product_id integer NOT NULL, -- foreign key of store_product.id
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL
);

--
-- Name: store_variation; Type: TABLE; 
-- This table contains details about the product variations
-- For a product, there can be many variations of "color" or "size"
-- Example colors: blue, black, yellow etc.
-- Possible sizes if the product is a clothing - small, medium, large, x-large
-- Possible sizes if the product is a footwear - 1,2,3,4,5,6,7,8,9,10,11,12,13
--

CREATE TABLE store_variation (
    id integer NOT NULL, -- primary key of the table store_variation
    variation_category character varying(100) NOT NULL, -- variation_category is either "color" or "size"
    variation_value character varying(100) NOT NULL, -- variation_value specifies the value of "color" or "size". This field has only lower case strings
    -- Example variation_value if variation_category='color': blue, black, yellow etc.
    -- Possible variation_value if variation_category='size' and product is a clothing - small, medium, large, x-large
    -- Possible variation_value if variation_category='size' and product is a footwear- 1,2,3,4,5,6,7,8,9,10,11,12,13  
    product_id integer NOT NULL -- foreign key of store_product.id
);

--
-- PostgreSQL database dump complete
--

