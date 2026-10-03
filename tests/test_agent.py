import json
import unittest
from unittest.mock import mock_open, patch

from fastapi import HTTPException

from app.agent import (
    GAME_WIKIS,
    _plain_wikitext,
    _relevant_passages,
    _wiki_for_game,
    search_game_sources,
    supported_games,
)


class RelevantPassageTests(unittest.TestCase):
    def test_route_question_keeps_route_instructions(self):
        passages = _relevant_passages(
            "From Ivarstead, cross the bridge and climb the 7000 steps to High Hrothgar.",
            "How do I get to High Hrothgar?",
            "Skyrim",
        )
        self.assertIn("Ivarstead", passages)

    def test_item_location_question_is_not_treated_as_route(self):
        passages = _relevant_passages(
            "Diamond ore is found deep underground and can be mined with an iron pickaxe.",
            "Where do I find diamond ore?",
            "Minecraft",
        )
        self.assertIn("mined", passages)

    def test_combat_question_rejects_lore_without_combat_help(self):
        passages = _relevant_passages(
            "Margit is a mysterious figure who appeared near the capital.",
            "How do I beat Margit?",
            "Elden Ring",
        )
        self.assertEqual("", passages)

    def test_wikitext_templates_keep_readable_entity_names(self):
        text = _plain_wikitext(
            "Travel to {{Link|Ivarstead}} and cross the bridge to {{Link|High Hrothgar}}."
        )
        self.assertIn("Ivarstead", text)
        self.assertIn("High Hrothgar", text)

    def test_breath_of_the_wild_ignores_conflicting_game_versions(self):
        passages = _relevant_passages(
            "To enter Zora's Domain, play Zelda's Lullaby. "
            "Travelers entering by foot cross the BotW Great Zora Bridge to Zora's Domain.",
            "How do I get to Zora's Domain?",
            "Breath of the Wild",
        )
        self.assertNotIn("Lullaby", passages)
        self.assertIn("BotW Great Zora Bridge", passages)


class GameSourceTests(unittest.TestCase):
    def test_registry_aliases_resolve_to_configured_wikis(self):
        self.assertEqual(
            GAME_WIKIS["fallout"],
            _wiki_for_game("Fallout 4"),
        )
        self.assertIn("Minecraft", supported_games())
        self.assertIsNone(_wiki_for_game("An unsupported game"))

    @patch(
        "app.agent.urlopen",
        new_callable=mock_open,
        read_data=json.dumps({
            "query": {
                "pages": [{
                    "title": "Margit, the Fell Omen",
                    "fullurl": "https://eldenring.fandom.com/wiki/Margit,_the_Fell_Omen",
                    "revisions": [{
                        "slots": {
                            "main": {
                                "content": (
                                    "Margit is a boss. His attacks leave openings to "
                                    "counter and deal damage."
                                )
                            }
                        }
                    }],
                }]
            }
        }),
    )
    def test_source_search_returns_topic_and_intent_matched_evidence(self, _urlopen):
        sources = search_game_sources("Elden Ring", "How do I beat Margit?")
        self.assertEqual(["Margit, the Fell Omen"], [source["title"] for source in sources])
        self.assertIn("attacks", sources[0]["content"])

    @patch(
        "app.agent.urlopen",
        new_callable=mock_open,
        read_data=json.dumps({
            "query": {
                "pages": [{
                    "title": "Margit, the Fell Omen",
                    "fullurl": "https://eldenring.fandom.com/wiki/Margit,_the_Fell_Omen",
                    "revisions": [{
                        "slots": {
                            "main": {
                                "content": "Margit is a mysterious figure who appeared near the capital."
                            }
                        }
                    }],
                }]
            }
        }),
    )
    def test_source_search_declines_when_passages_do_not_support_intent(self, _urlopen):
        with self.assertRaises(HTTPException) as context:
            search_game_sources("Elden Ring", "How do I beat Margit?")
        self.assertEqual(404, context.exception.status_code)

    @patch(
        "app.agent.urlopen",
        new_callable=mock_open,
        read_data=json.dumps({
            "query": {
                "pages": [{
                    "title": "Inazuma Shrine of Depths Key",
                    "fullurl": "https://genshin-impact.fandom.com/wiki/Inazuma_Shrine_of_Depths_Key",
                    "revisions": [{
                        "slots": {
                            "main": {
                                "content": (
                                    "The key is used to unlock the Shrines of Depths in Inazuma."
                                )
                            }
                        }
                    }],
                }]
            }
        }),
    )
    def test_unlock_search_declines_unrelated_subtopic(self, _urlopen):
        with self.assertRaises(HTTPException) as context:
            search_game_sources("Genshin Impact", "How do I unlock Inazuma?")
        self.assertEqual(404, context.exception.status_code)

    @patch(
        "app.agent.urlopen",
        new_callable=mock_open,
        read_data=json.dumps({
            "query": {
                "pages": [
                    {
                        "title": "Eye of Cthulhu",
                        "fullurl": "https://terraria.fandom.com/wiki/Eye_of_Cthulhu",
                        "revisions": [{
                            "slots": {"main": {
                                "content": "The Eye of Cthulhu can be summoned manually at night."
                            }}
                        }],
                    },
                    {
                        "title": "True Eye of Cthulhu",
                        "fullurl": "https://terraria.fandom.com/wiki/True_Eye_of_Cthulhu",
                        "revisions": [{
                            "slots": {"main": {
                                "content": "The True Eye of Cthulhu spawns during the Moon Lord fight."
                            }}
                        }],
                    },
                    {
                        "title": "Eye of Cthulhu/cs",
                        "fullurl": "https://terraria.fandom.com/wiki/Eye_of_Cthulhu/cs",
                        "revisions": [{
                            "slots": {"main": {
                                "content": "The Eye of Cthulhu can be summoned at night."
                            }}
                        }],
                    },
                ]
            }
        }),
    )
    def test_source_search_prefers_exact_topic_over_mod_variant(self, _urlopen):
        sources = search_game_sources(
            "Terraria",
            "How do I summon the Eye of Cthulhu?",
        )
        self.assertEqual(["Eye of Cthulhu"], [source["title"] for source in sources])


if __name__ == "__main__":
    unittest.main()
