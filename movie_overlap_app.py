# ============================================================
# Movie Cast Overlap Finder - Streamlit Web App
# ============================================================
# This is the web UI version of the movie overlap finder,
# with autocomplete search boxes powered by streamlit-searchbox.
#
# BEFORE YOU RUN THIS:
#   1. Make sure you have all libraries installed:
#        pip install requests streamlit streamlit-searchbox
#   2. Add your TMDB API key to .streamlit/secrets.toml:
#        TMDB_API_KEY = "your_key_here"
#   3. Run the app with:
#        streamlit run movie_overlap_app.py
# ============================================================

import requests
import streamlit as st
from streamlit_searchbox import st_searchbox
# st_searchbox is the autocomplete widget. It works by calling
# a function you provide every time the user types a character,
# and displays the returned suggestions in a dropdown.


# ============================================================
# API KEY & CONSTANTS
# ============================================================
API_KEY = st.secrets["TMDB_API_KEY"]
BASE_URL = "https://api.themoviedb.org/3"
POSTER_BASE_URL = "https://image.tmdb.org/t/p/w300"


# ============================================================
# SEARCH FUNCTION FOR THE AUTOCOMPLETE BOXES
# ============================================================
# st_searchbox requires a function that:
#   - accepts a single string argument (what the user typed)
#   - returns a list of options to show in the dropdown
#
# Each option can be a plain string, or a (label, value) tuple.
# We use tuples so the dropdown shows a human-readable label
# (e.g. "Shrek (2001)") but the selected value is the full
# movie dictionary — so we don't need to look it up again later.
# ============================================================
def search_movies_autocomplete(search_term):
    """
    Called automatically by st_searchbox every time the user types.
    Returns a list of (label, movie_dict) tuples for the dropdown.
    """
    # Don't bother searching if the user has typed fewer than 2 characters
    if not search_term or len(search_term) < 2:
        return []

    url = f"{BASE_URL}/search/movie"
    params = {"api_key": API_KEY, "query": search_term}

    try:
        response = requests.get(url, params=params)
        data = response.json()
    except Exception:
        # If the request fails for any reason, just return no suggestions
        return []

    suggestions = []
    # Loop through the top results (up to 7 so the list isn't too long)
    for movie in data.get("results", [])[:7]:
        # Get just the year from the "YYYY-MM-DD" release date string
        year = movie.get("release_date", "")[:4]
        year_str = f" ({year})" if year else ""

        # Build the label shown in the dropdown, e.g. "Shrek (2001)"
        label = f"{movie['title']}{year_str}"

        # Each suggestion is a (label, value) tuple.
        # The label is shown to the user; the value is what gets stored
        # when they select it — in this case, the full movie dictionary.
        suggestions.append((label, movie))

    return suggestions


# ============================================================
# API HELPER FUNCTIONS
# ============================================================

def get_cast(movie_id):
    """Fetch the full cast list for a movie given its TMDB ID."""
    url = f"{BASE_URL}/movie/{movie_id}/credits"
    params = {"api_key": API_KEY}
    response = requests.get(url, params=params)
    data = response.json()
    return data.get("cast", [])


def find_common_actors(cast1, cast2):
    """
    Compare two cast lists and return actors who appear in both.
    Returns a list of dictionaries with name, photo, and character info.
    """
    # Build a fast-lookup dictionary for movie 1's cast, keyed by actor ID
    cast1_by_id = {actor["id"]: actor for actor in cast1}

    common = []
    for actor in cast2:
        if actor["id"] in cast1_by_id:
            actor1_info = cast1_by_id[actor["id"]]
            common.append({
                "name": actor["name"],
                "profile_path": actor.get("profile_path"),
                "movie1_character": actor1_info.get("character", "Unknown role"),
                "movie2_character": actor.get("character", "Unknown role"),
            })

    return common


# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Movie Cast Overlap Finder",
    page_icon="🎬",
    layout="centered"
)

st.title("🎬 Movie Cast Overlap Finder")
st.write("Search for two movies below to find actors who appeared in both films.")
st.divider()


# ============================================================
# AUTOCOMPLETE SEARCH BOXES
# ============================================================
# st_searchbox() creates an input field with a live dropdown.
#
# Arguments:
#   search_movies_autocomplete  - the function to call as the user types
#   placeholder                 - greyed-out hint text in the box
#   key                         - a unique name (required when using
#                                 multiple searchboxes on the same page)
#
# Return value:
#   Whatever the user selected from the dropdown — in our case,
#   a full movie dictionary (the "value" from our tuple), or None
#   if they haven't selected anything yet.
# ============================================================
col1, col2 = st.columns(2)

with col1:
    st.write("**First Movie**")
    movie1 = st_searchbox(
        search_movies_autocomplete,
        placeholder="e.g. The Godfather",
        key="movie1_searchbox"
    )

with col2:
    st.write("**Second Movie**")
    movie2 = st_searchbox(
        search_movies_autocomplete,
        placeholder="e.g. Goodfellas",
        key="movie2_searchbox"
    )


# ============================================================
# SEARCH BUTTON
# ============================================================
search_clicked = st.button("🔍 Find Common Actors", use_container_width=True)

if search_clicked:

    # Make sure the user has selected a movie from each dropdown.
    # (movie1 and movie2 will be None if nothing has been selected yet)
    if not movie1 or not movie2:
        st.error("Please select a movie from the dropdown in each search box.")

    else:
        # ---- Show the two selected movies ----
        st.divider()
        st.subheader("Selected Movies")

        found_col1, found_col2 = st.columns(2)

        with found_col1:
            if movie1.get("poster_path"):
                st.image(POSTER_BASE_URL + movie1["poster_path"])
            year = movie1.get("release_date", "")[:4]
            st.write(f"**{movie1['title']}** ({year})")

        with found_col2:
            if movie2.get("poster_path"):
                st.image(POSTER_BASE_URL + movie2["poster_path"])
            year = movie2.get("release_date", "")[:4]
            st.write(f"**{movie2['title']}** ({year})")

        # ---- Fetch cast lists and compare ----
        with st.spinner("Fetching cast lists and comparing..."):
            cast1 = get_cast(movie1["id"])
            cast2 = get_cast(movie2["id"])
            common_actors = find_common_actors(cast1, cast2)

        # ---- Display results ----
        st.divider()

        if not common_actors:
            st.subheader("No Common Actors Found")
            st.write(
                f"No actors appear in both **{movie1['title']}** and **{movie2['title']}**."
            )
        else:
            st.subheader(f"✅ {len(common_actors)} Actor(s) in Common")

            for actor in common_actors:
                with st.container(border=True):
                    photo_col, info_col = st.columns([1, 4])

                    with photo_col:
                        if actor["profile_path"]:
                            st.image(POSTER_BASE_URL + actor["profile_path"])
                        else:
                            st.write("📷")

                    with info_col:
                        st.write(f"### {actor['name']}")
                        st.write(f"**{movie1['title']}:** {actor['movie1_character']}")
                        st.write(f"**{movie2['title']}:** {actor['movie2_character']}")
