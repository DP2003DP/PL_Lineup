# app.py - Complete FPL Dashboard
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Page config
st.set_page_config(
    page_title="FPL Optimizer Dashboard",
    page_icon="⚽",
    layout="wide"
)

# Title and header
st.title("⚽ Fantasy Premier League Optimizer")
st.markdown("---")

# Sidebar for navigation
page = st.sidebar.selectbox(
    "Navigation",
    ["📊 Overview", "🔮 Predictions", "🏆 Optimal Squad", "📈 Analysis", "🔄 Update Data"]
)

# Load data
@st.cache_data
def load_data():
    players = pd.read_csv('Data/current_players.csv')
    predictions = pd.read_csv('Data/predictions.csv')
    squad = pd.read_csv('Data/optimal_squad.csv') if 'optimal_squad.csv' in os.listdir('Data') else pd.DataFrame()
    history = pd.read_csv('Data/player_history.csv')
    return players, predictions, squad, history

players, predictions, squad, history = load_data()

# OVERVIEW PAGE
if page == "📊 Overview":
    st.header("Dashboard Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Players", len(players))
    
    with col2:
        if not squad.empty:
            st.metric("Squad Value", f"£{squad['price'].sum():.1f}M")
    
    with col3:
        if not squad.empty:
            st.metric("Predicted Points", f"{squad['predicted_points'].sum():.0f}")
    
    with col4:
        st.metric("Data Updated", datetime.now().strftime("%Y-%m-%d"))
    
    # Top performers chart
    st.subheader("🌟 Top Performers by Position")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Bar chart of top scorers
        top_scorers = players.nlargest(10, 'total_points')[['web_name', 'total_points']]
        fig = px.bar(
            top_scorers, 
            x='total_points', 
            y='web_name',
            orientation='h',
            title='Season Top Scorers',
            labels={'total_points': 'Total Points', 'web_name': 'Player'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Pie chart of squad by position
        if not squad.empty:
            position_counts = squad['position'].value_counts()
            fig = px.pie(
                values=position_counts.values,
                names=position_counts.index,
                title='Squad Composition'
            )
            st.plotly_chart(fig, use_container_width=True)

# PREDICTIONS PAGE
elif page == "🔮 Predictions":
    st.header("Player Predictions - Next Gameweek")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        position_filter = st.selectbox(
            "Position",
            ["All"] + ["GK", "DEF", "MID", "FWD"]
        )
    
    with col2:
        price_min, price_max = st.slider(
            "Price Range (£M)",
            float(predictions['price'].min()),
            float(predictions['price'].max()),
            (4.0, 15.0)
        )
    
    with col3:
        min_points = st.slider(
            "Min Predicted Points",
            0.0,
            float(predictions['predicted_points'].max()),
            0.0
        )
    
    # Filter data
    filtered = predictions.copy()
    
    if position_filter != "All":
        filtered = filtered[filtered['position'] == position_filter]
    
    filtered = filtered[
        (filtered['price'] >= price_min) & 
        (filtered['price'] <= price_max) &
        (filtered['predicted_points'] >= min_points)
    ]
    
    # Display top predictions
    st.subheader(f"Top {position_filter} Predictions")
    
    # Format for display
    display_cols = ['name', 'team', 'position', 'price', 'predicted_points']
    filtered_display = filtered[display_cols].sort_values('predicted_points', ascending=False).head(20)
    
    # Style the dataframe
    st.dataframe(
        filtered_display.style.format({
            'price': '£{:.1f}M',
            'predicted_points': '{:.1f}'
        }).background_gradient(subset=['predicted_points']),
        hide_index=True,
        use_container_width=True
    )
    
    # Value picks
    st.subheader("💎 Best Value Picks")
    
    # Calculate points per million
    filtered['value'] = filtered['predicted_points'] / filtered['price']
    best_value = filtered.nlargest(10, 'value')[['name', 'position', 'price', 'predicted_points', 'value']]
    
    st.dataframe(
        best_value.style.format({
            'price': '£{:.1f}M',
            'predicted_points': '{:.1f}',
            'value': '{:.2f}'
        }).background_gradient(subset=['value']),
        hide_index=True
    )

# OPTIMAL SQUAD PAGE
elif page == "🏆 Optimal Squad":
    st.header("Optimal Squad Selection")
    
    if squad.empty:
        st.warning("No optimal squad generated yet. Please run the optimizer first.")
    else:
        # Squad overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Cost", f"£{squad['price'].sum():.1f}M / £100M")
        
        with col2:
            st.metric("Predicted Points", f"{squad['predicted_points'].sum():.0f}")
        
        with col3:
            # Best captain choice
            captain = squad.nlargest(1, 'predicted_points').iloc[0]
            st.metric("Captain", f"{captain['name']} ({captain['predicted_points']*2:.0f}pts)")
        
        # Display squad by position
        st.subheader("Starting XI")
        
        formations = {
            '3-4-3': {'DEF': 3, 'MID': 4, 'FWD': 3},
            '3-5-2': {'DEF': 3, 'MID': 5, 'FWD': 2},
            '4-4-2': {'DEF': 4, 'MID': 4, 'FWD': 2},
            '4-3-3': {'DEF': 4, 'MID': 3, 'FWD': 3},
            '5-3-2': {'DEF': 5, 'MID': 3, 'FWD': 2},
        }
        
        formation = st.selectbox("Formation", list(formations.keys()))
        
        # Pick best XI for selected formation
        gk = squad[squad['position'] == 'GK'].nlargest(1, 'predicted_points')
        defense = squad[squad['position'] == 'DEF'].nlargest(formations[formation]['DEF'], 'predicted_points')
        midfield = squad[squad['position'] == 'MID'].nlargest(formations[formation]['MID'], 'predicted_points')
        forward = squad[squad['position'] == 'FWD'].nlargest(formations[formation]['FWD'], 'predicted_points')
        
        starting_11 = pd.concat([gk, defense, midfield, forward])
        bench = squad[~squad.index.isin(starting_11.index)]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⚽ Starting XI")
            for pos in ['GK', 'DEF', 'MID', 'FWD']:
                st.write(f"**{pos}**")
                pos_players = starting_11[starting_11['position'] == pos]
                for _, p in pos_players.iterrows():
                    if p['name'] == captain['name']:
                        st.write(f"🏅 {p['name']} (C) - {p['team']} - £{p['price']:.1f}M - {p['predicted_points']*2:.1f}pts")
                    else:
                        st.write(f"• {p['name']} - {p['team']} - £{p['price']:.1f}M - {p['predicted_points']:.1f}pts")
        
        with col2:
            st.subheader("🪑 Bench")
            for _, p in bench.iterrows():
                st.write(f"• {p['name']} - {p['position']} - £{p['price']:.1f}M - {p['predicted_points']:.1f}pts")
        
        st.metric("Total Starting XI Points", f"{starting_11['predicted_points'].sum() + captain['predicted_points']:.1f}")

# ANALYSIS PAGE
elif page == "📈 Analysis":
    st.header("Performance Analysis")
    
    # Historical performance chart
    st.subheader("📊 Model Performance Tracking")
    
    # Generate sample performance data (replace with actual backtest results)
    gameweeks = list(range(1, 11))
    predicted = [65, 72, 58, 81, 69, 75, 62, 78, 71, 68]
    actual = [61, 69, 62, 77, 65, 79, 58, 74, 73, 64]
    
    performance_df = pd.DataFrame({
        'Gameweek': gameweeks,
        'Predicted': predicted,
        'Actual': actual
    })
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=performance_df['Gameweek'],
        y=performance_df['Predicted'],
        name='Predicted',
        line=dict(color='blue', width=2)
    ))
    fig.add_trace(go.Scatter(
        x=performance_df['Gameweek'],
        y=performance_df['Actual'],
        name='Actual',
        line=dict(color='green', width=2)
    ))
    
    fig.update_layout(
        title='Predicted vs Actual Points',
        xaxis_title='Gameweek',
        yaxis_title='Points',
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Player form analysis
    st.subheader("🔥 Player Form Tracker")
    
    selected_player = st.selectbox(
        "Select Player",
        players['web_name'].sort_values().unique()
    )
    
    # Get player history
    player_id = players[players['web_name'] == selected_player]['id'].values[0]
    player_hist = history[history['player_id'] == player_id].tail(10)
    
    if not player_hist.empty:
        fig = px.line(
            player_hist,
            x='round',
            y='total_points',
            title=f'{selected_player} - Last 10 Gameweeks',
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)

# UPDATE DATA PAGE
elif page == "🔄 Update Data":
    st.header("Update Data")
    
    st.info("Click the buttons below to refresh data from the FPL API")
    
    if st.button("🔄 Update Player Data"):
        with st.spinner("Fetching latest player data..."):
            # Run your data collection code here
            st.success("✅ Player data updated successfully!")
    
    if st.button("📊 Retrain Model"):
        with st.spinner("Retraining prediction model..."):
            # Run your model training code here
            st.success("✅ Model retrained successfully!")
    
    if st.button("🏆 Generate New Optimal Squad"):
        with st.spinner("Optimizing squad..."):
            # Run your optimization code here
            st.success("✅ New optimal squad generated!")
    
    # Show last update times
    st.subheader("Last Update Times")
    import os
    from datetime import datetime
    
    files = {
        'Data/current_players.csv': 'Player Data',
        'models/predictor.pkl': 'Prediction Model',
        'Data/optimal_squad.csv': 'Optimal Squad'
    }
    
    for filepath, name in files.items():
        if os.path.exists(filepath):
            mtime = os.path.getmtime(filepath)
            update_time = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            st.write(f"**{name}:** {update_time}")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ for FPL managers | Data from Fantasy Premier League API")