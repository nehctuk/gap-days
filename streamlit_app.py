import streamlit as st

from gap_logic import get_stock_data, detect_gap_days, plot_stock_data

# Set Streamlit page configuration with a white background
st.set_page_config(
    page_title="Gap Stock Analysis",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Streamlit app
def main():
    st.title("Gap Stock Analysis")

    symbol = st.text_input("Enter stock ticker symbol:", value='SPY')
    last_n_gaps = st.text_input("Set how many gaps to display (None for all gaps):", value=None)

    if st.button("Fetch Data"):
        data = get_stock_data(symbol)

        # Detect gap days
        gap_events = detect_gap_days(data)

        # Plot the data with invalidation points
        fig = plot_stock_data(data, gap_events, last_n_gaps=last_n_gaps, symbol=symbol)

        st.plotly_chart(fig, use_container_width=True)  # Use full container width



if __name__ == "__main__":
    main()