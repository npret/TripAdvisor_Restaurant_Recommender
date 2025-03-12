import streamlit as st
import pandas as pd
import ast
import numpy as np
import base64


# Load cleaned dataset
@st.cache_data
def load_data():
    df = pd.read_csv("data/tripadvisor_cleaned.csv")
    df["Cuisine Style"] = df["Cuisine Style"].fillna("[]").apply(ast.literal_eval)  # Convert string lists to lists
    df["Reviews"] = df["Reviews"].fillna("[[],[]]").apply(ast.literal_eval)  # Convert reviews to lists
    return df

df = load_data()

# Sidebar filters
st.sidebar.title("🔍 Filter Options")
selected_city = st.sidebar.selectbox("Select a City", sorted(df["City"].unique()))

# Filter dataset by city
city_df = df[df["City"] == selected_city]

# Cuisine filter
all_cuisines = sorted(set([cuisine for sublist in city_df["Cuisine Style"] for cuisine in sublist]))
selected_cuisines = st.sidebar.multiselect("Filter by Cuisine Style", all_cuisines, default=[])

# Price range filter
price_options = sorted(df["Price Range"].dropna().unique())
selected_price = st.sidebar.multiselect("Filter by Price Range", price_options, default=[])

# Apply filters
filtered_df = city_df.copy()

if selected_cuisines:
    filtered_df = filtered_df[filtered_df["Cuisine Style"].apply(lambda x: any(c in x for c in selected_cuisines))]
if selected_price:
    filtered_df = filtered_df[filtered_df["Price Range"].isin(selected_price)]

# Calculate weighted ranking
filtered_df["Weighted Score"] = filtered_df["Rating"] * (
    1 + (np.log1p(filtered_df["Number of Reviews"]) / np.log1p(filtered_df["Number of Reviews"].max()))
)

# Sort by weighted ranking
filtered_df = filtered_df.sort_values(by="Weighted Score", ascending=False)

# Display best restaurant with full reviews and cuisines
if not filtered_df.empty:
    best_restaurant = filtered_df.iloc[0]
    
    # Get TripAdvisor full link
    tripadvisor_link = f"https://www.tripadvisor.com{best_restaurant['URL_TA']}"

    # Display featured section
    st.markdown(f"""
    ## 🏆 Best Pick: **{best_restaurant['Name']}**
    **Why?** {best_restaurant['Name']} is the top-rated choice for {", ".join(selected_cuisines) if selected_cuisines else "this city"}!
    """)

    # Display key details
    col1, col2, col3 = st.columns([1, 1, 1])
    col1.metric("⭐ Rating", f"{best_restaurant['Rating']}/5")
    col2.metric("📝 Reviews", f"{best_restaurant['Number of Reviews']} Reviews")
    col3.metric("💰 Price", best_restaurant['Price Range'])

    # Full Cuisine Style section
    st.subheader("🍽️ Cuisine Style")
    st.write(", ".join(best_restaurant["Cuisine Style"]))

    # 📝 Featured Reviews (Formatted Properly)
    st.subheader("📝 Featured Reviews")
    reviews = best_restaurant["Reviews"]

    if isinstance(reviews, list) and len(reviews) == 2:
        review_texts = reviews[0]
        review_dates = reviews[1]

        if review_texts and review_dates:
            for text, date in zip(review_texts, review_dates):
                st.markdown(
                    f"""
                    <div style="background-color:#d4edda; padding:10px; border-radius:5px; margin-bottom:5px;">
                        {text}<br>
                        <strong>{date}</strong>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.write("No reviews available.")
    else:
        st.write("No reviews available.")

    # View on TripAdvisor button
# Convert the image to Base64 so it loads properly inside HTML
def image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Convert the TripAdvisor logo to Base64
tripadvisor_logo_base64 = image_to_base64("visuals/tripadvisor-icon.png")

# Properly formatted button with inline logo
st.markdown(f"""
    <div style="display: flex; justify-content: center; margin-top: 10px;">
        <a href="{tripadvisor_link}" target="_blank" style="
            display: inline-flex;
            align-items: center;
            text-decoration: none;
            font-size: 16px;
            font-weight: bold;
            color: white;
            background-color: #34e0a1;
            padding: 10px 15px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
            transition: background 0.3s;
            line-height: normal;">
            <img src="data:image/png;base64,{tripadvisor_logo_base64}" width="20" height="20" style="margin-right: 8px;">
            View on TripAdvisor
        </a>
    </div>
""", unsafe_allow_html=True)






# Display main restaurant list
st.title(f"🍽️ Restaurants in {selected_city}")
st.write(f"Showing **{len(filtered_df)}** restaurants based on selected filters.")

# Reset index to start from 1
filtered_df.index = range(1, len(filtered_df) + 1)



filtered_df["Rating"] = filtered_df["Rating"].apply(lambda x: f"{x:.1f}")

st.dataframe(filtered_df[["Name", "Rating", "Number of Reviews", "Price Range", "Cuisine Style"]])
