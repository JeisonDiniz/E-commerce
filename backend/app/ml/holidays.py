"""
Calendário de datas comerciais brasileiras relevantes para moda/e-commerce,
no formato exigido pelo parâmetro `holidays` do Prophet
(colunas: holiday, ds, lower_window, upper_window — em dias).

Reflete o MESMO calendário usado para gerar o dataset sintético (Etapa 6),
o que é intencional: em um cenário real, esse calendário viria do
conhecimento de negócio do gestor da loja; aqui, como controlamos a geração
dos dados, podemos fornecer ao Prophet exatamente os eventos que de fato
influenciam a demanda — uma prática recomendada (curar o calendário de
feriados/eventos comerciais) e não um "vazamento" de informação, pois o
Prophet ainda precisa aprender a MAGNITUDE do efeito a partir dos dados.
"""
import pandas as pd


def _second_sunday_of_may(year: int) -> pd.Timestamp:
    first_of_may = pd.Timestamp(year=year, month=5, day=1)
    first_sunday = first_of_may + pd.Timedelta(days=(6 - first_of_may.weekday()) % 7)
    return first_sunday + pd.Timedelta(weeks=1)


def _last_friday_of_november(year: int) -> pd.Timestamp:
    last_of_nov = pd.Timestamp(year=year, month=11, day=30)
    offset = (last_of_nov.weekday() - 4) % 7
    return last_of_nov - pd.Timedelta(days=offset)


def build_brazilian_retail_holidays(years: range) -> pd.DataFrame:
    rows = []
    for year in years:
        rows.append({"holiday": "black_friday", "ds": _last_friday_of_november(year), "lower_window": -1, "upper_window": 1})
        rows.append({"holiday": "natal", "ds": pd.Timestamp(year, 12, 19), "lower_window": -4, "upper_window": 5})
        rows.append({"holiday": "dia_das_maes", "ds": _second_sunday_of_may(year), "lower_window": -3, "upper_window": 0})
        rows.append({"holiday": "dia_dos_namorados", "ds": pd.Timestamp(year, 6, 12), "lower_window": -2, "upper_window": 0})
        rows.append({"holiday": "volta_as_aulas", "ds": pd.Timestamp(year, 1, 26), "lower_window": -6, "upper_window": 15})

    return pd.DataFrame(rows)
