# ============================================================
# Movie Cast Overlap Finder - Streamlit Web App
# ============================================================
# This is the web UI version of the movie overlap finder.
#
# BEFORE YOU RUN THIS:
#   1. Make sure you have both libraries installed:
#        pip install requests streamlit
#   2. Replace the placeholder below with your TMDB API key
#   3. Run the app with:
#        streamlit run movie_overlap_app.py
#   4. It will automatically open in your browser!
# ============================================================

import requests   # For making calls to the TMDB API
import streamlit as st  # For building the web UI

# ============================================================
# CONFIGURATION
# ============================================================
# ============================================================
# API KEY - loaded securely from Streamlit's secrets system.
#
# Locally:  stored in .streamlit/secrets.toml (never shared)
# Online:   entered in the Streamlit Community Cloud dashboard
# ============================================================
API_KEY = st.secrets["TMDB_API_KEY"]
BASE_URL = "https://api.themoviedb.org/3"
POSTER_BASE_URL = "https://image.tmdb.org/t/p/w300"  # Base URL for movie poster images


# ============================================================
# API FUNCTIONS (same logic as the original script)
# ============================================================

def search_movie(title):
    """Search TMDB for a movie by title. Returns the best match, or None."""
    url = f"{BASE_URL}/search/movie"
    params = {"api_key": API_KEY, "query": title}
    response = requests.get(url, params=params)
    data = response.json()

    if not data["results"]:
        return None

    return data["results"][0]


def get_cast(movie_id):
    """Fetch the full cast list for a movie given its TMDB ID."""
    url = f"{BASE_URL}/movie/{movie_id}/credits"
    params = {"api_key": API_KEY}
    response = requests.get(url, params=params)
    data = response.json()
    return data.get("cast", [])


def find_common_actors(cast1, cast2, movie1_title, movie2_title):
    """
    Compare two cast lists and return actors who appear in both.
    Returns a list of dictionaries with actor info.
    """
    # Build a lookup dictionary for movie 1's cast (keyed by actor ID)
    cast1_by_id = {actor["id"]: actor for actor in cast1}

    common = []
    for actor in cast2:
        if actor["id"] in cast1_by_id:
            actor1_info = cast1_by_id[actor["id"]]
            common.append({
                "name": actor["name"],
                "profile_path": actor.get("profile_path"),  # Photo URL path
                "movie1_character": actor1_info.get("character", "Unknown role"),
                "movie2_character": actor.get("character", "Unknown role"),
            })

    return common


# ============================================================
# PAGE CONFIGURATION
# Streamlit lets you configure the browser tab title and layout.
# This must be the first Streamlit command in the file.
# ============================================================
st.set_page_config(
    page_title="Movie Cast Overlap Finder",
    page_icon="🎬",
    layout="centered"
)


# ============================================================
# APP HEADER
# st.title() and st.write() display text on the page.
# The "🎬" is just an emoji — feel free to change it!
# ============================================================
st.title("🎬 Movie Cast Overlap Finder")
st.write("Enter two movies below to find actors who appeared in both films.")

# A horizontal divider line
st.divider()


# ============================================================
# MOVIE INPUT FIELDS
# st.columns() splits the page into side-by-side columns.
# col1 and col2 are the two halves of the screen.
# ============================================================
col1, col2 = st.columns(2)

# Each column gets its own text input field.
# The value the user types is stored in title1 and title2.
with col1:
    title1 = st.text_input("First Movie", placeholder="e.g. The Godfather")

with col2:
    title2 = st.text_input("Second Movie", placeholder="e.g. Goodfellas")


# ============================================================
# SEARCH BUTTON
# st.button() creates a clickable button.
# Everything inside the "if" block only runs when it's clicked.
# "use_container_width=True" makes the button stretch full width.
# ============================================================
search_clicked = st.button("🔍 Find Common Actors", use_container_width=True)

if search_clicked:

    # Make sure the user actually typed something in both fields
    if not title1 or not title2:
        st.error("Please enter both movie titles before searching.")

    else:
        # ---- Step 1: Search for both movies ----
        # st.spinner() shows a loading animation while the code inside runs
        with st.spinner("Searching for movies..."):
            movie1 = search_movie(title1)
            movie2 = search_movie(title2)

        # If either movie wasn't found, show an error and stop
        if not movie1:
            st.error(f"Couldn't find a movie matching **{title1}**. Try a different spelling.")
            st.stop()

        if not movie2:
            st.error(f"Couldn't find a movie matching **{title2}**. Try a different spelling.")
            st.stop()

        # ---- Step 2: Show the two movies we found ----
        st.divider()
        st.subheader("Movies Found")

        # Display each movie in its own column with poster and title
        found_col1, found_col2 = st.columns(2)

        with found_col1:
            # Show the movie poster if one exists
            if movie1.get("poster_path"):
                st.image(POSTER_BASE_URL + movie1["poster_path"])
            year = movie1.get("release_date", "")[:4]  # Just the year from "YYYY-MM-DD"
            st.write(f"**{movie1['title']}** ({year})")

        with found_col2:
            if movie2.get("poster_path"):
                st.image(POSTER_BASE_URL + movie2["poster_path"])
            year = movie2.get("release_date", "")[:4]
            st.write(f"**{movie2['title']}** ({year})")

        # ---- Step 3: Fetch cast and find overlaps ----
        with st.spinner("Fetching cast lists and comparing..."):
            cast1 = get_cast(movie1["id"])
            cast2 = get_cast(movie2["id"])
            common_actors = find_common_actors(cast1, cast2, movie1["title"], movie2["title"])

        # ---- Step 4: Display results ----
        st.divider()

        if not common_actors:
            st.subheader("No Common Actors Found")
            st.write(
                f"No actors appear in both **{movie1['title']}** and **{movie2['title']}**."
            )
        else:
            st.subheader(f"✅ {len(common_actors)} Actor(s) in Common")

            # Display each shared actor in a styled card
            for actor in common_actors:
                # st.container() groups elements together visually
                with st.container(border=True):
                    # Columns: photo on left, details on right
                    photo_col, info_col = st.columns([1, 4])

                    with photo_col:
                        if actor["profile_path"]:
                            st.image(POSTER_BASE_URL + actor["profile_path"])
                        else:
                            # If no photo, show a placeholder
                            st.write("📷")

                    with info_col:
                        st.write(f"### {actor['name']}")
                        st.write(f"**{movie1['title']}:** {actor['movie1_character']}")
                        st.write(f"**{movie2['title']}:** {actor['movie2_character']}")
