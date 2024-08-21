import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import re
import sys

# Database connection details
def get_db_connection():
    """Establish a database connection and return the connection object."""
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="yogeshwaran",
            database="redbus_project"
        )
    except mysql.connector.Error as err:
        st.error(f"Error connecting to database: {err}")
        sys.exit()

# Fetch route links based on route name
def get_route_link(route_name):
    """Fetch the route link for a given route name."""
    conn = get_db_connection()
    try:
        query = "SELECT route_link FROM bus_route_information WHERE bus_route = %s"
        df = pd.read_sql(query, conn, params=(route_name,))
        if not df.empty:
            return df['route_link'].iloc[0]
        else:
            st.warning(f"No route link found for route: {route_name}.")
            return None
    except Exception as e:
        st.error(f"Error fetching route link: {e}")
        return None  # Return None in case of error
    finally:
        conn.close()

# Function to clean fare column
def clean_fare(fare):
    """Extract numeric value from fare string."""
    digits = re.findall(r'\d+', str(fare))
    return int(''.join(digits)) if digits else 0

# Fetch bus information based on route link, departure time range, and price range
def get_bus_information(route_link, start_time, end_time, min_fare, max_fare):
    """Fetch bus information based on route link and specified criteria."""
    conn = get_db_connection()
    try:
        query = """
        SELECT bus_name, bus_type, 
               departure_time, 
               duration, 
               reaching_time, 
               star_rating, price, seats_available
        FROM bus_information
        WHERE route_link = %s
        AND TIME(departure_time) BETWEEN %s AND %s
        AND price BETWEEN %s AND %s
        """
        df = pd.read_sql(query, conn, params=(route_link, start_time, end_time, min_fare, max_fare))
        return df if df is not None else pd.DataFrame()  # Ensure return type is DataFrame
    except Exception as e:
        st.error(f"Error fetching bus information: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of error
    finally:
        conn.close()

# Load available routes
def get_routes():
    """Load available routes from the database."""
    conn = get_db_connection()
    try:
        query = "SELECT DISTINCT bus_route FROM bus_route_information"
        df = pd.read_sql(query, conn)
        return df['bus_route'].tolist() if df is not None else []  # Ensure return type is list
    except Exception as e:
        st.error(f"Error fetching routes: {e}")
        return []  # Return an empty list in case of error
    finally:
        conn.close()

# Generate list of time options with 1-hour intervals
def generate_time_options(start_hour=0, end_hour=23):
    """Generate time options from start_hour to end_hour in 1-hour intervals."""
    times = []
    current_time = datetime.strptime(f"{start_hour:02d}:00", "%H:%M")
    end_time = datetime.strptime(f"{end_hour:02d}:59", "%H:%M")
    while current_time <= end_time:
        times.append(current_time.strftime("%H:%M"))
        current_time += timedelta(hours=1)
    return times

# Generate list of price options with 1000 intervals
def generate_price_options(start_price=0, end_price=10000, interval=1000):
    """Generate price options from start_price to end_price with specified intervals."""
    return list(range(start_price, end_price + interval, interval))

# Streamlit application
st.title("Book Your Bus")

# Initialize session state
if 'booking_success' not in st.session_state:
    st.session_state.booking_success = False

# Sidebar for inputs
st.sidebar.header("Tell Us About Your Preference")

routes = ["Choose an option"] + get_routes()
selected_route = st.sidebar.selectbox("Select a route:", routes)

if selected_route != "Choose an option":
    time_options = generate_time_options()
    start_time = st.sidebar.selectbox("Select start time", time_options, index=time_options.index("00:00"))
    end_time = st.sidebar.selectbox("Select end time", time_options, index=time_options.index("23:00"))

    price_options = generate_price_options()
    min_fare = st.sidebar.selectbox("Select minimum fare", price_options, index=0)
    max_fare = st.sidebar.selectbox("Select maximum fare", price_options, index=len(price_options) - 1)

    submit_button = st.sidebar.button("Get Bus Information")

    if submit_button:
        # Get route link from Table 1
        route_link = get_route_link(selected_route)
        
        if route_link:
            # Fetch and display bus information using route link, time range, and price range
            bus_info_df = get_bus_information(route_link, start_time, end_time, min_fare, max_fare)
            
            if not bus_info_df.empty:
                # Display route, departure time, and price range in columns
                with st.container():
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.subheader(f"Route: {selected_route}")
                    
                    with col2:
                        st.write(f"**Departure Time Range:** {start_time} - {end_time}")
                        st.write(f"**Price Range:** {min_fare} - {max_fare}")

                st.write("---")

                # Display each bus's details with a side container for additional info
                for index, row in bus_info_df.iterrows():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Bus Name:** {row['bus_name']}")
                        st.write(f"**Bus Type:** {row['bus_type']}")
                        st.write(f"**Departure Time:** {row['departure_time']}")
                        st.write(f"**Arrival Time:** {row['reaching_time']}")
                        st.write(f"**Duration:** {row['duration']}")

                    with col2:
                        st.write(f"**Rating:** {row['star_rating']}")
                        st.write(f"**Fare:** {row['price']}")
                        st.write(f"**Seats Available:** {row['seats_available']}")
                        # Add a book button for each bus entry
                        if st.button(f"Book {row['bus_name']}", key=f"book_{index}"):
                            # Set session state to show success page
                            st.session_state.booking_success = True
                            st.experimental_rerun()  # Refresh the page to show the booking success message
                        
                    st.write("---")
                
            else:
                st.write(f"No bus information found for route between {start_time} and {end_time}, and fare between {min_fare} and {max_fare}.")
        else:
            st.write(f"No route link found for the selected route: {selected_route}.")
else:
    st.write("Please select a valid route.")