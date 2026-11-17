# -*- coding: utf-8 -*-
"""
Created on Tue Nov 17 11:19:39 2026

@author: Luis José López
"""

import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

st.set_page_config(
    page_title="Finanzas Personales", page_icon="📊", layout="wide"
)


# Cargar datos procesados
@st.cache_data(ttl=60)
def cargar_datos():
  with open("datos_dashboard.json", "r", encoding="utf-8") as f:
    return json.load(f)


data = cargar_datos()
fechas = data["fechas"]
df_mensual = pd.DataFrame(data["mensual"])

# ==========================================
# ENCABEZADO Y SELECTOR DE MES
# ==========================================
col_titulo, col_filtro = st.columns([3, 1])
with col_titulo:
  st.title("Panel de Finanzas Personales")
with col_filtro:
  mes_sel = st.selectbox(
      "Mes de cierre", options=list(reversed(fechas)), index=0
  )

fila_actual = df_mensual[df_mensual["fecha"] == mes_sel].iloc[0]

# ==========================================
# FILA SUPERIOR: 5 TARJETAS RESUMEN (KPIs)
# ==========================================
k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Presupuesto Mensual", f"RD$ {data['presupuesto_total']:,.0f}")
k2.metric(
    "Resultado Neto",
    f"RD$ {fila_actual['resultado']:,.0f}",
    delta=f"Ingresos: {fila_actual['ingresos']:,.0f}",
)
k3.metric("Tasa de Ahorro", f"{fila_actual['tasa_ahorro']:.1f}%")
k4.metric("Patrimonio Neto", f"RD$ {fila_actual['patrimonio_neto']:,.0f}")
k5.metric("Fondo de Emergencia", f"{fila_actual['fe_meses']:.1f} meses")

st.divider()

# Filtrar últimos 12 meses hasta el mes seleccionado
idx_sel = fechas.index(mes_sel)
ultimos_12 = fechas[max(0, idx_sel - 11) : idx_sel + 1]
df_12m = df_mensual[df_mensual["fecha"].isin(ultimos_12)]

# ==========================================
# FILA 1 DE GRÁFICOS (ARRIBA IZQ Y DER)
# ==========================================
g1, g2 = st.columns(2)

with g1:
  st.subheader("Resultado Mensual y Tasa de Ahorro (12M)")
  fig1 = make_subplots(specs=[[{"secondary_y": True}]])

  fig1.add_trace(
      go.Bar(
          x=df_12m["fecha"],
          y=df_12m["resultado"],
          name="Resultado (RD$)",
          marker_color="#2E86C1",
      ),
      secondary_y=False,
  )
  fig1.add_trace(
      go.Scatter(
          x=df_12m["fecha"],
          y=df_12m["tasa_ahorro"],
          name="Tasa Ahorro (%)",
          mode="lines+markers",
          line=dict(color="#28B463", width=3),
      ),
      secondary_y=True,
  )
  fig1.update_yaxes(title_text="RD$", secondary_y=False)
  fig1.update_yaxes(title_text="Tasa Ahorro (%)", secondary_y=True)
  fig1.update_layout(
      height=360,
      margin=dict(l=10, r=10, t=30, b=10),
      legend=dict(orientation="h", y=1.12),
  )
  st.plotly_chart(fig1, use_container_width=True)

with g2:
  st.subheader("Composición de Activos")
  df_act = pd.DataFrame(data["activos_detalle"])
  df_act_grupo = df_act.groupby("Nivel_2")[mes_sel].sum().reset_index()
  df_act_grupo = df_act_grupo[df_act_grupo[mes_sel] > 0]

  fig2 = px.pie(
      df_act_grupo,
      values=mes_sel,
      names="Nivel_2",
      hole=0.5,
      color_discrete_sequence=px.colors.qualitative.Set2,
  )
  fig2.update_traces(textposition="inside", textinfo="percent+label")
  fig2.update_layout(
      height=360, margin=dict(l=10, r=10, t=30, b=10), showlegend=False
  )
  st.plotly_chart(fig2, use_container_width=True)

# ==========================================
# FILA 2 DE GRÁFICOS (DEBAJO IZQ Y DER)
# ==========================================
g3, g4 = st.columns(2)

with g3:
  # 1. Título dinámico usando el mes obtenido de la celda B1 de tu Excel
  mes_etiqueta = data.get("mes_presupuesto", "mes")
  st.subheader(f"Presupuesto mensual ({mes_etiqueta})")
  
  df_gvp = pd.DataFrame(data["gastos_vs_pres"])
  
  # Agrupamos por Nivel_3 (que contiene el detalle de tus gastos presupuestados)
  df_gvp_cat = df_gvp.groupby("Nivel_3")[["Gasto_Mes_Corriente", "Presupuesto"]].sum().reset_index()
  df_gvp_cat = df_gvp_cat[
      (df_gvp_cat["Gasto_Mes_Corriente"] > 0) | (df_gvp_cat["Presupuesto"] > 0)
  ]
  df_gvp_cat = df_gvp_cat.sort_values(by="Gasto_Mes_Corriente", ascending=True)

  fig3 = go.Figure()
  # Gasto real en barras
  fig3.add_trace(
      go.Bar(
          y=df_gvp_cat["Nivel_3"],
          x=df_gvp_cat["Gasto_Mes_Corriente"],
          name="Gasto Real",
          orientation="h",
          marker_color="#FF4B4B",
      )
  )
  # Presupuesto con un guion / línea vertical de marcador
  fig3.add_trace(
      go.Scatter(
          y=df_gvp_cat["Nivel_3"],
          x=df_gvp_cat["Presupuesto"],
          name="Presupuesto",
          mode="markers",
          marker=dict(symbol="line-ns-open", size=16, line=dict(width=4), color="#1B2631"),
      )
  )
  # Eliminar las gridlines (líneas de cuadrícula) del gráfico
  fig3.update_layout(
      height=380,
      margin=dict(l=10, r=10, t=30, b=10),
      legend=dict(orientation="h", y=1.12),
      xaxis=dict(showgrid=False, zeroline=False),
      yaxis=dict(showgrid=False, zeroline=False),
  )
  st.plotly_chart(fig3, use_container_width=True)

with g4:
  st.subheader("Evolución Patrimonio Neto por Grupo (12M)")
  df_pat = pd.DataFrame(data["patrimonio_grupos"])
  for f in ultimos_12:
    df_pat.loc[df_pat["Nivel_1"] == "Pasivos", f] *= -1

  df_pat_melt = df_pat.melt(
      id_vars=["Nivel_1", "Nivel_2"],
      value_vars=ultimos_12,
      var_name="Fecha",
      value_name="Monto",
  )

  # Diccionario directo: asigna cada categoría de tu Excel a su color exacto
  colores_por_categoria = {
      "Efectivo y equivalentes": "#FFC000",
      "Banco": "#A6CAEC",
      "Inversiones": "#1C7629",
      "Cuentas por cobrar": "#55D768",
      "Propiedades": "#A6A6A6",
      "Otros activos": "#7F7F7F",
      "Tarjeta de crédito": "#092442",
      "Préstamos": "#F6AC26",
      "Cuentas por pagar": "#F83520"
  }

  fig4 = px.bar(
      df_pat_melt,
      x="Fecha",
      y="Monto",
      color="Nivel_2",
      barmode="relative",
      color_discrete_map=colores_por_categoria,  # Usamos el mapa directo por nombre
      category_orders={
          "Nivel_2": [
              "Propiedades",
              "Otros activos",
              "Cuentas por cobrar",
              "Banco",
              "Inversiones",
              "Efectivo y equivalentes",
              "Tarjeta de crédito",
              "Préstamos",
              "Cuentas por pagar",
          ]
      },
  )
  fig4.update_layout(
      height=380,
      margin=dict(l=10, r=10, t=30, b=10),
      legend=dict(orientation="h", y=-0.2),
      xaxis=dict(showgrid=False),
      yaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
  )
  st.plotly_chart(fig4, use_container_width=True)