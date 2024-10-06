import pandas as pd
from yahooquery import Ticker
import plotly.graph_objs as go
import plotly.offline as pyo
import holidays

# Function to pull stock data
def get_stock_data(symbol, period="1y"):
    ticker = Ticker(symbol)
    data = ticker.history(period=period)
    data = data.reset_index()
    data['date'] = pd.to_datetime(data['date'])  # Ensure 'date' column is in datetime format
    return data

# Function to detect gap days (upside and downside)
def detect_gap_days(data):
    gap_events = []
    for i in range(1, len(data)):
        prev_high = data['high'].iloc[i-1]
        prev_low = data['low'].iloc[i-1]
        prev_close = data['close'].iloc[i-1]
        current_open = data['open'].iloc[i]

        # Detect gap-up days (open higher than the previous day's high)
        if current_open > prev_high:
            # Only include the gap if it's not invalidated on the same day
            if data['low'].iloc[i] > prev_close:
                gap_events.append((i, prev_close, 'gap_up'))  # Store the index, close price, and event type

        # Detect gap-down days (open lower than the previous day's low)
        elif current_open < prev_low:
            # Only include the gap if it's not invalidated on the same day
            if data['high'].iloc[i] < prev_close:
                gap_events.append((i, prev_close, 'gap_down'))  # Store the index, close price, and event type

    return gap_events

# Function to find the point where the gap line gets crossed and invalidated, including the first candle
def find_invalidation_point(data, start_index, level, is_gap_up):
    for i in range(start_index, len(data)):
        if is_gap_up and data['low'].iloc[i] <= level:
            return data['date'].iloc[i]
        elif not is_gap_up and data['high'].iloc[i] >= level:
            return data['date'].iloc[i]
    return data['date'].iloc[-1]  # No invalidation, extend till the last point

# Function to filter last N gap events, regardless of type (up or down)
def filter_last_n_gaps(gap_events, last_n_gaps):
    if last_n_gaps is None:
        return gap_events
    return gap_events[-last_n_gaps:]  # Select the last N events, sorted by date

# Function to generate stock market holidays for a given year
def get_stock_market_holidays(year):
    us_holidays = holidays.US(years=int(year))
    stock_market_holidays = [
        'New Year\'s Day',
        'Martin Luther King Jr. Day',
        'Presidents\' Day',
        'Good Friday',
        'Memorial Day',
        'Independence Day',
        'Labor Day',
        'Thanksgiving',
        'Christmas Day'
    ]
    holiday_dates = [date for date, name in us_holidays.items() if name in stock_market_holidays]
    return holiday_dates

# Function to plot stock data and gap day lines with invalidation
def plot_stock_data(data, gap_events, last_n_gaps=None, exclude_holidays=True, symbol=None):
    # Filter to show only last N gap events if specified
    gap_events = filter_last_n_gaps(gap_events, last_n_gaps)

    fig = go.Figure()

    # Create candlestick chart
    fig.add_trace(go.Candlestick(x=data['date'],
                                 open=data['open'],
                                 high=data['high'],
                                 low=data['low'],
                                 close=data['close'],
                                 name="Candlestick"))

    # Add lines for gap events (up and down) with invalidation
    for index, level, gap_type in gap_events:
        is_gap_up = gap_type == 'gap_up'
        # Start invalidation check from the same candle
        end_date = find_invalidation_point(data, index, level, is_gap_up)
        color = "green" if is_gap_up else "red"
        name = f"Gap Up {data['date'].iloc[index]}" if is_gap_up else f"Gap Down {data['date'].iloc[index]}"

        fig.add_trace(go.Scatter(
            x=[data['date'].iloc[index], end_date],
            y=[level, level],
            mode="lines",
            line=dict(color=color, dash='dash'),
            name=name
        ))

    # Get holidays automatically for the year range in the data
    years = pd.to_datetime(data['date']).dt.year.unique()
    all_holidays = []
    if exclude_holidays and not symbol.endswith("-USD"):
        for year in years:
            all_holidays.extend(get_stock_market_holidays(year))

    # Determine if weekends and holidays should be skipped based on the symbol
    skip_weekends = not symbol.endswith("-USD")
    skip_holidays = exclude_holidays and not symbol.endswith("-USD")

    # Create rangebreaks list (avoid None elements)
    rangebreaks = []
    if skip_weekends:
        rangebreaks.append(dict(bounds=["sat", "mon"]))  # Skip weekends unless symbol has "-USD"
    if skip_holidays:
        rangebreaks.append(dict(values=all_holidays))  # Conditionally hide holidays

    # Update layout to remove weekends if applicable, remove holidays, add whitespace, and set price on the right
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        xaxis=dict(
            rangebreaks=rangebreaks,
            range=[data['date'].min(), data['date'].max() + pd.Timedelta(days=5)]  # Add 5 days of whitespace
        ),
        yaxis=dict(
            side="right"  # Display price on the right side
        ),
        title=f"Stock Price and Gap Days with Invalidation for {symbol}",
        xaxis_title="Date",
        yaxis_title="Price"
    )

    # Show the plot
    pyo.plot(fig)
    return fig
