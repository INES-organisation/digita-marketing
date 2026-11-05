import importlib.util
import os

spec = importlib.util.spec_from_file_location("fix_slugs", os.path.join(os.path.dirname(__file__), "..", "tools", "fix_slugs.py"))
fix_slugs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fix_slugs)


def test_duplicates_keep_the_longest_under_the_right_address():
    articles = [
        {"id": 1, "slug": "stratgie-nft", "title": "Stratégie NFT : Guide Complet", "length": 2660},
        {"id": 2, "slug": "strategie-nft", "title": "Stratégie NFT : Guide Complet", "length": 402},
        {"id": 3, "slug": "intgration-crm", "title": "Intégration CRM : Guide Complet", "length": 900},
        {"id": 4, "slug": "seo-local", "title": "SEO local : Guide Complet", "length": 900},
        {"id": 5, "slug": "ab-testing", "title": "A/B testing : Guide Complet", "length": 900},  # lisible : gardée
    ]
    formations = [{"id": 9, "slug": "formation-effets-spciaux", "title": "Formation Effets spéciaux"},
                  {"id": 8, "slug": "formation-seo", "title": "Formation SEO"},
                  {"id": 7, "slug": "formation-uxui-design", "title": "Formation UX/UI Design"}]
    renames, archived, moves = fix_slugs.plan(articles, formations)
    assert archived == [2]
    assert renames["blog_articles"] == [(1, "stratgie-nft", "strategie-nft"), (3, "intgration-crm", "integration-crm")]
    assert renames["formations"] == [(9, "formation-effets-spciaux", "formation-effets-speciaux")]
    assert ("article", "stratgie-nft", "strategie-nft") in moves and ("article", "seo-local", "seo-local") not in moves
