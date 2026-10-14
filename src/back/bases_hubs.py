"""
Módulo de Inteligência Geográfica: Bases e Hubs
Responsável por geocodificação em cache e cálculo dos polígonos de cobertura.
"""

import math
import os
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

CACHE_FILE = "data/geocache.csv"


def carregar_cache() -> pd.DataFrame:
    """Pergunta ao sistema: Já temos coordenadas salvas de consultas anteriores?"""
    if os.path.exists(CACHE_FILE):
        return pd.read_csv(CACHE_FILE)
    return pd.DataFrame(columns=["Cidade_UF", "Latitude", "Longitude"])


def salvar_cache(df_cache: pd.DataFrame):
    """Ordem: Salve as coordenadas encontradas para nunca mais precisar consultar a internet por elas."""
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    df_cache.drop_duplicates(subset=["Cidade_UF"], inplace=True)
    df_cache.to_csv(CACHE_FILE, index=False)


def obter_coordenadas(cidade: str, uf: str, df_cache: pd.DataFrame, geolocator) -> tuple:
    """Pergunta ao software: Qual a coordenada dessa cidade?
    Se não estiver no cache, consulte a API pública.
    """
    chave = f"{cidade.strip()} - {uf.strip()}"

    # 1. Verifica no cache local
    filtro = df_cache[df_cache["Cidade_UF"] == chave]
    if not filtro.empty:
        return (
            filtro.iloc[0]["Latitude"],
            filtro.iloc[0]["Longitude"],
            df_cache,
        )

    # 2. Se não estiver no cache, consulta via OpenStreetMap/Nominatim
    try:
        query = f"{cidade}, {uf}, Brasil"
        location = geolocator(query)
        if location:
            lat, lon = location.latitude, location.longitude
            novo_registro = pd.DataFrame([{"Cidade_UF": chave, "Latitude": lat, "Longitude": lon}])
            df_cache = pd.concat([df_cache, novo_registro], ignore_index=True)
            salvar_cache(df_cache)
            return lat, lon, df_cache
    except Exception:
        pass

    return None, None, df_cache


def processar_base_hubs(caminho_excel="data/bases_hubs.xlsx") -> pd.DataFrame:
    """Função Principal do Back-end:
    Lê a planilha, limpa os dados e garante que todas as linhas tenham coordenadas.
    """
    if not os.path.exists(caminho_excel):
        # Fallback caso a planilha esteja na raiz do projeto
        if os.path.exists("bases_hubs.xlsx"):
            caminho_excel = "bases_hubs.xlsx"
        else:
            return pd.DataFrame()

    df = pd.read_excel(caminho_excel)

    # Limpeza defensiva das colunas de texto
    for col in ["Tipo", "UF", "Cidade"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    df_cache = carregar_cache()
    geolocator = RateLimiter(
        Nominatim(user_agent="logcare_painel_operacional").geocode, 
        min_delay_seconds=1
    )

    lats, lons = [], []
    for _, row in df.iterrows():
        lat, lon, df_cache = obter_coordenadas(
            str(row.get("Cidade", "")), 
            str(row.get("UF", "")), 
            df_cache, 
            geolocator
        )
        lats.append(lat)
        lons.append(lon)

    df["Latitude"] = lats
    df["Longitude"] = lons

    return df.dropna(subset=["Latitude", "Longitude"])


def gerar_circulos_cobertura(df: pd.DataFrame, raio_km=50, num_pontos=36) -> dict:
    """Cálculo Matemático Geodésico: Cria polígonos circulares para a camada de raio de suporte."""
    R = 6371.0  # Raio médio da Terra em km
    features = []

    for _, row in df.iterrows():
        lat, lon = row["Latitude"], row["Longitude"]
        coords = []
        for i in range(num_pontos + 1):
            ang = math.radians(float(i) / num_pontos * 360)
            d = raio_km / R
            lat_rad, lon_rad = math.radians(lat), math.radians(lon)

            lat_p = math.asin(
                math.sin(lat_rad) * math.cos(d)
                + math.cos(lat_rad) * math.sin(d) * math.cos(ang)
            )
            lon_p = lon_rad + math.atan2(
                math.sin(ang) * math.sin(d) * math.cos(lat_rad),
                math.cos(d) - math.sin(lat_rad) * math.sin(lat_p),
            )
            coords.append([math.degrees(lon_p), math.degrees(lat_p)])

        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [coords]},
        })

    return {"type": "FeatureCollection", "features": features}