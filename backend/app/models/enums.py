"""
Bindings dos tipos ENUM nativos do PostgreSQL (criados em database/schema.sql)
para os models SQLAlchemy. `create_type=False` em todos porque o tipo já
existe no banco — o SQLAlchemy deve apenas referenciá-lo, nunca tentar
criá-lo novamente (isso quebraria em cima de um banco já provisionado pelo
schema.sql).
"""
import enum

from sqlalchemy import Enum as PgEnum


class UserRole(str, enum.Enum):
    customer = "customer"
    staff = "staff"
    manager = "manager"
    admin = "admin"


class GenderType(str, enum.Enum):
    masculino = "masculino"
    feminino = "feminino"
    unissex = "unissex"
    infantil = "infantil"


class SeasonType(str, enum.Enum):
    verao = "verao"
    inverno = "inverno"
    outono = "outono"
    primavera = "primavera"
    o_ano_todo = "o_ano_todo"


class SizeType(str, enum.Enum):
    PP = "PP"
    P = "P"
    M = "M"
    G = "G"
    GG = "GG"
    XG = "XG"
    UNICO = "UNICO"
    T34 = "34"
    T36 = "36"
    T38 = "38"
    T40 = "40"
    T42 = "42"
    T44 = "44"
    T46 = "46"
    T48 = "48"


class MovementType(str, enum.Enum):
    entrada = "entrada"
    saida = "saida"
    ajuste = "ajuste"
    devolucao = "devolucao"


class OrderStatus(str, enum.Enum):
    pendente = "pendente"
    pago = "pago"
    processando = "processando"
    enviado = "enviado"
    entregue = "entregue"
    cancelado = "cancelado"


class PaymentMethod(str, enum.Enum):
    cartao_credito = "cartao_credito"
    cartao_debito = "cartao_debito"
    pix = "pix"
    boleto = "boleto"


class PaymentStatus(str, enum.Enum):
    pendente = "pendente"
    aprovado = "aprovado"
    recusado = "recusado"
    estornado = "estornado"


class ModelType(str, enum.Enum):
    prophet = "prophet"
    random_forest = "random_forest"


class SuggestionStatus(str, enum.Enum):
    pendente = "pendente"
    aprovada = "aprovada"
    rejeitada = "rejeitada"


def pg_enum(python_enum: type[enum.Enum], pg_name: str) -> PgEnum:
    """Helper para declarar uma coluna Enum apontando para um tipo já existente no Postgres."""
    return PgEnum(python_enum, name=pg_name, create_type=False, values_callable=lambda e: [i.value for i in e])