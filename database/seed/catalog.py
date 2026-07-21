"""
Definição estática do catálogo sintético (categorias, produtos e variantes)
usado tanto para gerar o dataset de vendas (para treino/teste local dos
modelos de ML) quanto para popular o banco Postgres via `seed_database.py`.

Mantido em um único módulo, sem dependência de banco, para poder ser
reaproveitado em notebooks/scripts de experimentação de ML.
"""
from dataclasses import dataclass, field

SIZE_SETS: dict[str, list[str]] = {
    "roupa": ["PP", "P", "M", "G", "GG", "XG"],
    "unico": ["UNICO"],
}

COLORS = [
    "Preto",
    "Branco",
    "Azul Marinho",
    "Cinza Mescla",
    "Vermelho",
    "Verde Militar",
    "Bege",
    "Rosa",
]


@dataclass
class ProductTemplate:
    name: str
    brand: str
    gender: str  # masculino | feminino | unissex | infantil
    season: str  # verao | inverno | outono | primavera | o_ano_todo
    base_price: float
    size_set: str = "roupa"  # chave em SIZE_SETS
    n_colors: int = 3


@dataclass
class CategoryDef:
    slug: str
    name: str
    parent_slug: str | None
    products: list[ProductTemplate] = field(default_factory=list)


CATALOG: list[CategoryDef] = [
    CategoryDef(
        "camisetas", "Camisetas", None,
        [
            ProductTemplate("Camiseta Básica Algodão", "Urbana Co.", "unissex", "o_ano_todo", 39.90),
            ProductTemplate("Camiseta Estampada Streetwear", "Urbana Co.", "masculino", "verao", 59.90),
            ProductTemplate("Camiseta Gola V Feminina", "Bela Moda", "feminino", "o_ano_todo", 49.90),
            ProductTemplate("Camiseta Longline", "Urbana Co.", "masculino", "verao", 69.90),
        ],
    ),
    CategoryDef(
        "camisas", "Camisas", None,
        [
            ProductTemplate("Camisa Social Slim", "Classica Wear", "masculino", "o_ano_todo", 129.90),
            ProductTemplate("Camisa Xadrez Flanela", "Classica Wear", "masculino", "inverno", 99.90),
            ProductTemplate("Camisa Feminina Cropped", "Bela Moda", "feminino", "verao", 89.90),
        ],
    ),
    CategoryDef(
        "calcas", "Calças", None,
        [
            ProductTemplate("Calça Jeans Skinny", "Bela Moda", "feminino", "o_ano_todo", 149.90),
            ProductTemplate("Calça Jeans Reta", "Classica Wear", "masculino", "o_ano_todo", 159.90),
            ProductTemplate("Calça Cargo", "Urbana Co.", "unissex", "o_ano_todo", 169.90),
            ProductTemplate("Calça Moletom", "Conforto Basics", "unissex", "inverno", 119.90),
        ],
    ),
    CategoryDef(
        "vestidos", "Vestidos", None,
        [
            ProductTemplate("Vestido Midi Floral", "Bela Moda", "feminino", "primavera", 129.90),
            ProductTemplate("Vestido Curto Verão", "Bela Moda", "feminino", "verao", 99.90),
            ProductTemplate("Vestido Tricot", "Bela Moda", "feminino", "inverno", 139.90),
        ],
    ),
    CategoryDef(
        "shorts-bermudas", "Shorts e Bermudas", None,
        [
            ProductTemplate("Bermuda Sarja", "Classica Wear", "masculino", "verao", 89.90),
            ProductTemplate("Short Jeans Feminino", "Bela Moda", "feminino", "verao", 79.90),
            ProductTemplate("Bermuda Moletom", "Conforto Basics", "unissex", "verao", 69.90),
        ],
    ),
    CategoryDef(
        "jaquetas-casacos", "Jaquetas e Casacos", None,
        [
            ProductTemplate("Jaqueta Jeans", "Urbana Co.", "unissex", "outono", 179.90),
            ProductTemplate("Casaco de Frio Puffer", "Conforto Basics", "unissex", "inverno", 249.90),
            ProductTemplate("Corta-Vento", "Urbana Co.", "masculino", "inverno", 149.90),
        ],
    ),
    CategoryDef(
        "moletons", "Moletons", None,
        [
            ProductTemplate("Moletom Canguru", "Conforto Basics", "unissex", "inverno", 139.90),
            ProductTemplate("Moletom Careca Oversized", "Urbana Co.", "unissex", "inverno", 129.90),
        ],
    ),
    CategoryDef("acessorios", "Acessórios", None, []),
    CategoryDef(
        "bones", "Bonés", "acessorios",
        [ProductTemplate("Boné Aba Reta", "Urbana Co.", "unissex", "o_ano_todo", 49.90, size_set="unico", n_colors=4)],
    ),
    CategoryDef(
        "cintos", "Cintos", "acessorios",
        [ProductTemplate("Cinto de Couro", "Classica Wear", "masculino", "o_ano_todo", 59.90, size_set="unico", n_colors=2)],
    ),
]


def _slugify_part(text: str) -> str:
    replacements = str.maketrans("áàâãéèêíïóôõöúçñ", "aaaaeeeiiooooucn")
    return text.lower().translate(replacements).replace(" ", "-")


def build_flat_catalog() -> tuple[list[dict], list[dict], list[dict]]:
    """
    Retorna (categories, products, variants) como listas de dicts prontos
    para inserção — cada dict usa `slug`/`sku` como chave natural (as
    chaves reais em UUID só existem depois de inseridos no Postgres).
    """
    categories: list[dict] = []
    products: list[dict] = []
    variants: list[dict] = []

    for cat in CATALOG:
        categories.append({"slug": cat.slug, "name": cat.name, "parent_slug": cat.parent_slug})

        for p_idx, product in enumerate(cat.products):
            product_slug = f"{cat.slug}-{_slugify_part(product.name)}"
            products.append(
                {
                    "slug": product_slug,
                    "category_slug": cat.slug,
                    "name": product.name,
                    "brand": product.brand,
                    "gender": product.gender,
                    "season": product.season,
                    "base_price": product.base_price,
                    "description": f"{product.name} da linha {product.brand}, ideal para o dia a dia.",
                }
            )

            sizes = SIZE_SETS[product.size_set]
            colors = COLORS[: product.n_colors]
            for color in colors:
                for size in sizes:
                    sku = f"{product_slug}-{size}-{_slugify_part(color)}".upper()[:60]
                    price = round(product.base_price, 2)
                    variants.append(
                        {
                            "sku": sku,
                            "product_slug": product_slug,
                            "category_slug": cat.slug,
                            "gender": product.gender,
                            "season": product.season,
                            "size": size,
                            "color": color,
                            "price": price,
                            "cost_price": round(price * 0.5, 2),
                        }
                    )

    return categories, products, variants
