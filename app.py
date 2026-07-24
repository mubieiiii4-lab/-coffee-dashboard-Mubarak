import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Afficionado Coffee Roasters — Product Analytics", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("transactions_clean.csv")
    if "revenue" not in df.columns:
        df["revenue"] = df["transaction_qty"] * df["unit_price"]
    return df

df = load_data()

st.title("☕ Afficionado Coffee Roasters")
st.caption("Product Optimization & Revenue Contribution Analysis")

st.sidebar.header("Filters")
categories = sorted(df["product_category"].unique())
sel_categories = st.sidebar.multiselect("Product Category", categories, default=categories)

df_cat_filtered = df[df["product_category"].isin(sel_categories)]
types_available = sorted(df_cat_filtered["product_type"].unique())
sel_types = st.sidebar.multiselect("Product Type", types_available, default=types_available)

stores = sorted(df["store_location"].unique())
sel_stores = st.sidebar.multiselect("Store Location", stores, default=stores)

top_n = st.sidebar.slider("Top-N Products", min_value=5, max_value=50, value=15, step=5)

mask = (
    df["product_category"].isin(sel_categories)
    & df["product_type"].isin(sel_types)
    & df["store_location"].isin(sel_stores)
)
fdf = df[mask]

if fdf.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

total_revenue = fdf["revenue"].sum()
total_units = fdf["transaction_qty"].sum()
n_products = fdf["product_detail"].nunique()
avg_price = fdf["unit_price"].mean()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Revenue", f"${total_revenue:,.0f}")
k2.metric("Units Sold", f"{total_units:,.0f}")
k3.metric("Active Products", f"{n_products}")
k4.metric("Avg Unit Price", f"${avg_price:,.2f}")

st.divider()

prod = (
    fdf.groupby(["product_category", "product_type", "product_detail"])
    .agg(revenue=("revenue", "sum"), units=("transaction_qty", "sum"),
         transactions=("transaction_id", "count"))
    .reset_index()
    .sort_values("revenue", ascending=False)
)
prod["revenue_share_pct"] = (prod["revenue"] / total_revenue * 100).round(2)

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Product Ranking", "🥧 Category Breakdown", "🔍 Popularity vs Revenue", "📈 Revenue Concentration"]
)

with tab1:
    st.subheader(f"Top {top_n} Products by Revenue")
    top_rev = prod.head(top_n)
    fig = px.bar(top_rev.sort_values("revenue"), x="revenue", y="product_detail",
                 orientation="h", color="product_category")
    fig.update_layout(height=max(400, top_n * 28))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Full Product Table")
    st.dataframe(prod, use_container_width=True, hide_index=True)

with tab2:
    cat = (fdf.groupby("product_category").agg(revenue=("revenue", "sum")).reset_index()
           .sort_values("revenue", ascending=False))
    fig3 = px.pie(cat, names="product_category", values="revenue", hole=0.4)
    st.plotly_chart(fig3, use_container_width=True)

with tab3:
    fig5 = px.scatter(prod, x="units", y="revenue", size="transactions",
                       color="product_category", hover_name="product_detail")
    st.plotly_chart(fig5, use_container_width=True)

with tab4:
    pareto = prod.sort_values("revenue", ascending=False).reset_index(drop=True)
    pareto["cum_pct"] = pareto["revenue"].cumsum() / total_revenue * 100
    pareto["product_rank"] = range(1, len(pareto) + 1)
    n_for_80 = min((pareto["cum_pct"] <= 80).sum() + 1, len(pareto))
    st.info(f"{n_for_80} of {len(pareto)} products generate 80% of revenue.")
    fig6 = px.line(pareto, x="product_rank", y="cum_pct", markers=True)
    fig6.add_hline(y=80, line_dash="dash", line_color="red")
    st.plotly_chart(fig6, use_container_width=True)