from typing import Dict, List, Optional

class AcademicReferenceSystem:
    """System to integrate academic and technical references into proposals"""
    
    def __init__(self, project_info: Dict, tor_content: str):
        self.project = project_info
        self.tor_content = tor_content
        self.reference_database = self._load_reference_database()
        self.guatemala_data_sources = self._load_guatemala_sources()
        
    def _load_reference_database(self) -> Dict:
        return {
            "international_frameworks": {
                "SDGs": {
                    "source": "United Nations Sustainable Development Goals",
                    "url": "https://sdgs.un.org/goals",
                    "relevance": "Global development framework",
                    "key_indicators": ["SDG 1: No Poverty", "SDG 8: Decent Work", "SDG 10: Reduced Inequalities"],
                    "citation": "United Nations. (2015). Transforming our world: the 2030 Agenda for Sustainable Development. UN General Assembly Resolution 70/1."
                },
                "Paris_Agreement": {
                    "source": "Paris Agreement on Climate Change",
                    "url": "https://unfccc.int/process-and-meetings/the-paris-agreement/the-paris-agreement",
                    "relevance": "Climate action framework",
                    "citation": "UNFCCC. (2015). Paris Agreement. United Nations Framework Convention on Climate Change."
                },
                "Sendai_Framework": {
                    "source": "Sendai Framework for Disaster Risk Reduction",
                    "url": "https://www.undrr.org/publication/sendai-framework-disaster-risk-reduction-2015-2030",
                    "relevance": "Disaster risk reduction",
                    "citation": "UNDRR. (2015). Sendai Framework for Disaster Risk Reduction 2015-2030."
                }
            },
            "development_theories": {
                "capability_approach": {
                    "author": "Amartya Sen",
                    "theory": "Capability Approach to Development",
                    "relevance": "Human development focus",
                    "citation": "Sen, A. (1999). Development as Freedom. Oxford University Press.",
                    "key_concepts": ["Human capabilities", "Functionings", "Agency", "Freedom"]
                },
                "asset_based_development": {
                    "authors": "John McKnight & John Kretzmann",
                    "theory": "Asset-Based Community Development (ABCD)",
                    "relevance": "Community-driven development",
                    "citation": "McKnight, J. & Kretzmann, J. (1993). Building Communities from the Inside Out. ACTA Publications.",
                    "key_concepts": ["Community assets", "Local capacity", "Citizen-led development"]
                },
                "social_capital": {
                    "author": "James Coleman, Pierre Bourdieu, Robert Putnam",
                    "theory": "Social Capital Theory",
                    "relevance": "Community organization and networks",
                    "citation": "Putnam, R. (2000). Bowling Alone: The Collapse and Revival of American Community. Simon & Schuster.",
                    "key_concepts": ["Social networks", "Trust", "Reciprocity", "Civic engagement"]
                }
            },
            "methodological_approaches": {
                "participatory_development": {
                    "source": "Institute of Development Studies",
                    "methodology": "Participatory Rural Appraisal (PRA)",
                    "citation": "Chambers, R. (1994). The origins and practice of participatory rural appraisal. World Development, 22(7), 953-969.",
                    "tools": ["Community mapping", "Seasonal calendars", "Wealth ranking", "Problem trees"]
                },
                "theory_of_change": {
                    "source": "ActKnowledge and Aspen Institute",
                    "methodology": "Theory of Change",
                    "citation": "Weiss, C. H. (1995). Nothing as Practical as Good Theory: Exploring Theory-based Evaluation. American Journal of Evaluation, 16(1), 65-75.",
                    "components": ["Long-term outcomes", "Preconditions", "Assumptions", "Activities"]
                },
                "results_based_management": {
                    "source": "OECD-DAC",
                    "methodology": "Results-Based Management",
                    "citation": "OECD. (2002). Glossary of Key Terms in Evaluation and Results Based Management. OECD Publications.",
                    "framework": ["Impact", "Outcomes", "Outputs", "Activities", "Inputs"]
                }
            },
            "evaluation_methods": {
                "most_significant_change": {
                    "authors": "Rick Davies & Jess Dart",
                    "methodology": "Most Significant Change Technique",
                    "citation": "Davies, R. & Dart, J. (2005). The 'Most Significant Change' (MSC) Technique: A Guide to Its Use. www.mande.co.uk/docs/MSCGuide.pdf",
                    "application": "Participatory evaluation"
                },
                "outcome_harvesting": {
                    "author": "Ricardo Wilson-Grau",
                    "methodology": "Outcome Harvesting",
                    "citation": "Wilson-Grau, R. (2015). Outcome Harvesting. Better Evaluation.",
                    "application": "Outcome identification and verification"
                },
                "developmental_evaluation": {
                    "author": "Michael Quinn Patton",
                    "methodology": "Developmental Evaluation",
                    "citation": "Patton, M. Q. (2010). Developmental Evaluation: Applying Complexity Concepts to Enhance Innovation and Use. Guilford Press.",
                    "application": "Complex adaptive systems"
                }
            }
        }
    
    def _load_guatemala_sources(self) -> Dict:
        return {
            "national_statistics": {
                "INE": {
                    "institution": "Instituto Nacional de Estadística",
                    "data_types": ["Demographics", "Poverty", "Employment", "Education", "Health"],
                    "key_publications": [
                        "XII Censo Nacional de Población y VII de Vivienda 2018",
                        "Encuesta Nacional de Condiciones de Vida (ENCOVI) 2019",
                        "Encuesta Nacional de Empleo e Ingresos (ENEI) 2019"
                    ],
                    "poverty_data": {
                        "national_poverty_rate": 59.3,
                        "extreme_poverty_rate": 23.4,
                        "rural_poverty_rate": 76.1,
                        "urban_poverty_rate": 42.1
                    },
                    "citation": "INE. (2019). Encuesta Nacional de Condiciones de Vida 2019. Instituto Nacional de Estadística de Guatemala."
                },
                "SEGEPLAN": {
                    "institution": "Secretaría de Planificación y Programación de la Presidencia",
                    "key_documents": [
                        "Plan Nacional de Desarrollo K'atun: nuestra Guatemala 2032",
                        "Política General de Desarrollo 2020-2024"
                    ],
                    "strategic_axes": [
                        "Riqueza para todas y todos",
                        "Bienestar para la gente",
                        "Recursos naturales hoy y para el futuro",
                        "El Estado como garante de los derechos humanos"
                    ],
                    "citation": "SEGEPLAN. (2014). Plan Nacional de Desarrollo K'atun: nuestra Guatemala 2032. SEGEPLAN."
                },
                "BANGUAT": {
                    "institution": "Banco de Guatemala",
                    "economic_indicators": {
                        "gdp_growth_2023": 3.2,
                        "inflation_rate_2023": 6.2,
                        "exchange_rate_2024": 7.75,
                        "remittances_gdp": 15.3
                    },
                    "citation": "BANGUAT. (2024). Estadísticas Macroeconómicas. Banco de Guatemala."
                }
            },
            "academic_institutions": {
                "FLACSO_Guatemala": {
                    "institution": "Facultad Latinoamericana de Ciencias Sociales - Guatemala",
                    "research_areas": ["Governance", "Gender", "Indigenous peoples", "Migration"],
                    "key_studies": [
                        "Mapa de la exclusión social en Guatemala",
                        "Análisis de la pobreza multidimensional en Guatemala"
                    ],
                    "citation": "FLACSO Guatemala. (2019). Mapa de la exclusión social en Guatemala. FLACSO-Guatemala."
                },
                "URL": {
                    "institution": "Universidad Rafael Landívar",
                    "institutes": ["IDIES - Instituto de Investigación y Proyección sobre el Estado"],
                    "publications": ["Perfil de la pobreza en Guatemala", "Análisis del gasto público social"],
                    "citation": "IDIES-URL. (2018). Perfil de la pobreza en Guatemala. Universidad Rafael Landívar."
                },
                "ASIES": {
                    "institution": "Asociación de Investigación y Estudios Sociales",
                    "expertise": ["Political analysis", "Economic studies", "Social policy"],
                    "publications": ["Guatemala en Cifras", "Compendio de Historia de Guatemala"],
                    "citation": "ASIES. (2020). Guatemala en Cifras 2020. Asociación de Investigación y Estudios Sociales."
                }
            },
            "international_presence": {
                "UNDP_Guatemala": {
                    "reports": ["Human Development Report Guatemala 2019/2020"],
                    "hdi_2019": 0.663,
                    "hdi_rank": 127,
                    "citation": "PNUD Guatemala. (2020). Informe Nacional de Desarrollo Humano 2019/2020. PNUD."
                },
                "World_Bank": {
                    "country_studies": ["Guatemala Poverty Assessment 2018", "Guatemala: Jobs and Social Protection"],
                    "poverty_line_2019": 12.2,
                    "gini_coefficient": 48.3,
                    "citation": "World Bank. (2018). Guatemala Poverty Assessment. World Bank Group."
                },
                "ECLAC": {
                    "studies": ["Panorama Social de América Latina", "Agenda 2030 en Guatemala"],
                    "sdg_implementation": "Voluntary National Review 2021",
                    "citation": "CEPAL. (2021). Panorama Social de América Latina 2020. Comisión Económica para América Latina y el Caribe."
                }
            },
            "sector_specific": {
                "education": {
                    "MINEDUC_data": {
                        "net_enrollment_primary": 87.4,
                        "completion_rate_primary": 73.1,
                        "literacy_rate_adult": 81.5,
                        "literacy_rate_youth": 92.8
                    },
                    "citation": "MINEDUC. (2019). Anuario Estadístico de la Educación 2019. Ministerio de Educación de Guatemala."
                },
                "health": {
                    "MSPAS_data": {
                        "maternal_mortality": 95,
                        "infant_mortality": 23,
                        "chronic_malnutrition_under5": 46.5,
                        "vaccination_coverage": 85.2
                    },
                    "citation": "MSPAS. (2020). Memoria de Labores 2019. Ministerio de Salud Pública y Asistencia Social."
                },
                "agriculture": {
                    "MAGA_data": {
                        "agricultural_gdp": 13.3,
                        "rural_employment_agric": 67.8,
                        "food_insecurity": 15.8,
                        "coffee_production": 3.9
                    },
                    "citation": "MAGA. (2019). El Agro en Cifras 2019. Ministerio de Agricultura, Ganadería y Alimentación."
                }
            }
        }
    
    def generate_contextualized_references(self, topic_area: str, geographic_focus: Optional[str] = None) -> Dict:
        relevant_refs = {
            "international_frameworks": [],
            "theoretical_foundations": [],
            "methodological_approaches": [],
            "evaluation_methods": [],
            "guatemala_context": [],
            "sector_specific": [],
            "data_sources": []
        }
        
        topic_mapping = {
            "community_development": {
                "theories": ["capability_approach", "asset_based_development", "social_capital"],
                "methods": ["participatory_development", "theory_of_change"],
                "evals": ["most_significant_change", "outcome_harvesting"],
                "frameworks": ["SDGs"],
                "sectors": ["education", "health", "agriculture"]
            },
            "governance": {
                "theories": ["social_capital"],
                "methods": ["participatory_development"],
                "evals": ["most_significant_change", "developmental_evaluation"],
                "frameworks": ["SDGs"],
                "sectors": ["education"]
            },
            "economic_development": {
                "theories": ["capability_approach"],
                "methods": ["results_based_management", "theory_of_change"],
                "evals": ["outcome_harvesting"],
                "frameworks": ["SDGs"],
                "sectors": ["agriculture", "education"]
            },
            "climate_resilience": {
                "theories": ["asset_based_development"],
                "methods": ["participatory_development", "results_based_management"],
                "evals": ["outcome_harvesting"],
                "frameworks": ["Paris_Agreement", "Sendai_Framework"],
                "sectors": ["agriculture"]
            }
        }
        
        detected_topic = self._detect_project_topic()
        topic_refs = topic_mapping.get(detected_topic, topic_mapping["community_development"])
        
        for framework in topic_refs["frameworks"]:
            if framework in self.reference_database["international_frameworks"]:
                relevant_refs["international_frameworks"].append(
                    self.reference_database["international_frameworks"][framework]
                )
        
        for theory in topic_refs["theories"]:
            if theory in self.reference_database["development_theories"]:
                relevant_refs["theoretical_foundations"].append(
                    self.reference_database["development_theories"][theory]
                )
        
        for method in topic_refs["methods"]:
            if method in self.reference_database["methodological_approaches"]:
                relevant_refs["methodological_approaches"].append(
                    self.reference_database["methodological_approaches"][method]
                )
        
        for ev in topic_refs["evals"]:
            if ev in self.reference_database["evaluation_methods"]:
                relevant_refs["evaluation_methods"].append(
                    self.reference_database["evaluation_methods"][ev]
                )
        
        relevant_refs["guatemala_context"] = [
            self.guatemala_data_sources["national_statistics"]["INE"],
            self.guatemala_data_sources["national_statistics"]["SEGEPLAN"],
            self.guatemala_data_sources["academic_institutions"]["FLACSO_Guatemala"],
            self.guatemala_data_sources["international_presence"]["UNDP_Guatemala"]
        ]
        
        for sector in topic_refs["sectors"]:
            if sector in self.guatemala_data_sources["sector_specific"]:
                relevant_refs["sector_specific"].append({
                    "sector": sector,
                    "data": self.guatemala_data_sources["sector_specific"][sector]
                })
        
        return relevant_refs
    
    def _detect_project_topic(self) -> str:
        content_lower = self.tor_content.lower()
        if any(word in content_lower for word in ["governance", "democracy", "participation", "citizen"]):
            return "governance"
        elif any(word in content_lower for word in ["economic", "livelihood", "income", "employment"]):
            return "economic_development"
        elif any(word in content_lower for word in ["climate", "disaster", "resilience", "adaptation"]):
            return "climate_resilience"
        else:
            return "community_development"
    
    def generate_literature_review_section(self, topic_area: str) -> str:
        refs = self.generate_contextualized_references(topic_area)
        literature_review = f"""
## MARCO TEÓRICO Y REVISIÓN DE LITERATURA

### Fundamentos Teóricos

El presente proyecto se fundamenta en marcos teóricos consolidados del desarrollo internacional que han demostrado eficacia en contextos similares al guatemalteco.
"""
        for theory in refs["theoretical_foundations"]:
            literature_review += f"""
#### {theory.get('theory', 'Teoría de Desarrollo')}

{theory.get('author', 'Diversos autores')} propone que {self._generate_theory_explanation(theory)}. Esta aproximación es particularmente relevante para el contexto guatemalteco dado que {self._contextualize_theory_guatemala(theory)}.

**Referencia:** {theory.get('citation', 'Cita no disponible')}
"""
        literature_review += "\n### Marcos Normativos Internacionales\n\n"
        literature_review += "El proyecto se alinea con los siguientes instrumentos internacionales:\n"
        for framework in refs["international_frameworks"]:
            indicators = framework.get('key_indicators', [])
            indicators_txt = ', '.join(indicators) if indicators else 'Indicadores relevantes'
            literature_review += f"""
**{framework.get('source', 'Marco Internacional')}:** {framework.get('relevance', 'Relevancia no especificada')}. Los indicadores clave incluyen: {indicators_txt}.

*Cita:* {framework.get('citation', 'Cita no disponible')}
"""
        literature_review += "\n### Contexto Nacional y Evidencia Empírica\n"
        ine_data = self.guatemala_data_sources["national_statistics"]["INE"]
        literature_review += f"""
Según el Instituto Nacional de Estadística de Guatemala (2019), el país presenta los siguientes indicadores de desarrollo:

- **Pobreza general:** {ine_data['poverty_data']['national_poverty_rate']}%
- **Pobreza extrema:** {ine_data['poverty_data']['extreme_poverty_rate']}%
- **Pobreza rural:** {ine_data['poverty_data']['rural_poverty_rate']}% (vs. {ine_data['poverty_data']['urban_poverty_rate']}% urbana)
"""
        undp_data = self.guatemala_data_sources["international_presence"]["UNDP_Guatemala"]
        literature_review += f"""
El Índice de Desarrollo Humano de Guatemala es de {undp_data['hdi_2019']}, ubicando al país en la posición {undp_data['hdi_rank']} a nivel mundial (PNUD, 2020).
"""
        for sector_info in refs["sector_specific"]:
            sector = sector_info["sector"]
            data = sector_info["data"]
            if sector == "education":
                literature_review += f"""
#### Contexto Educativo

Según el Ministerio de Educación (2019): escolarización primaria {data['MINEDUC_data']['net_enrollment_primary']}%, finalización {data['MINEDUC_data']['completion_rate_primary']}%, alfabetización adulta {data['MINEDUC_data']['literacy_rate_adult']}%.
"""
            elif sector == "health":
                literature_review += f"""
#### Contexto de Salud

Mortalidad materna {data['MSPAS_data']['maternal_mortality']} por 100,000 nacidos vivos; desnutrición crónica <5 años {data['MSPAS_data']['chronic_malnutrition_under5']}%.
"""
        literature_review += "\n### Justificación Metodológica\n"
        for method in refs["methodological_approaches"]:
            literature_review += f"""
#### {method.get('methodology', 'Metodología')}

{method.get('citation', 'Diversos estudios')} demuestran que {self._generate_method_explanation(method)}. En el contexto guatemalteco, esta metodología es particularmente apropiada porque {self._contextualize_method_guatemala(method)}.
"""
        if refs["evaluation_methods"]:
            literature_review += "\n### Enfoques de Monitoreo y Evaluación\n"
            for ev in refs["evaluation_methods"]:
                literature_review += f"""
#### {ev.get('methodology', 'Método de Evaluación')}

{ev.get('citation', 'Referencia no disponible')}. Su aplicación es pertinente porque facilita {self._generate_method_explanation({'methodology': ev.get('methodology','')})}.
"""
        literature_review += """
### Síntesis del Marco Conceptual

La combinación de enfoques teóricos, marcos normativos, evidencia contextual y métodos de evaluación proporciona una base sólida para el diseño e implementación del proyecto.
"""
        return literature_review
    
    def _generate_theory_explanation(self, theory: Dict) -> str:
        explanations = {
            "capability_approach": "el desarrollo debe enfocarse en expandir las capacidades humanas y las libertades reales de las personas",
            "asset_based_development": "las comunidades poseen activos y capacidades internas que deben ser identificados y movilizados",
            "social_capital": "las redes sociales, la confianza y la reciprocidad son recursos fundamentales para el desarrollo"
        }
        key = theory.get('theory', '').replace(' ', '_').lower()
        return explanations.get(key, "proporciona un marco conceptual sólido para el desarrollo comunitario")
    
    def _contextualize_theory_guatemala(self, theory: Dict) -> str:
        contextualizations = {
            "capability_approach": "Guatemala presenta brechas en capacidades básicas, especialmente en poblaciones rurales e indígenas",
            "asset_based_development": "las comunidades poseen diversidad cultural y estructuras organizativas tradicionales valiosas",
            "social_capital": "el tejido social comunitario basado en reciprocidad es una fortaleza para el desarrollo local"
        }
        key = theory.get('theory', '').replace(' ', '_').lower()
        return contextualizations.get(key, "es apropiada para el contexto sociocultural guatemalteco")
    
    def _generate_method_explanation(self, method: Dict) -> str:
        explanations = {
            "participatory_rural_appraisal_(pra)": "la participación activa asegura pertinencia, apropiación y sostenibilidad",
            "theory_of_change": "la construcción de una teoría del cambio identifica supuestos y rutas causales hacia el impacto",
            "results-based_management": "el enfoque en resultados medibles permite seguimiento y adaptación oportuna",
            "most_significant_change_technique": "la recolección de historias de cambio significativo y su validación participativa",
            "outcome_harvesting": "la identificación retrospectiva de cambios y la verificación de contribuciones",
            "developmental_evaluation": "la adaptación continua en sistemas complejos durante la innovación"
        }
        key = method.get('methodology', '').replace(' ', '_').lower()
        return explanations.get(key, "ha demostrado efectividad en contextos de desarrollo similares")
    
    def _contextualize_method_guatemala(self, method: Dict) -> str:
        contextualizations = {
            "participatory_rural_appraisal_(pra)": "respeta estructuras de decisión comunitaria y procesos de consulta tradicionales",
            "theory_of_change": "permite incorporar cosmovisiones y lógicas causales propias de las comunidades",
            "results-based_management": "facilita rendición de cuentas a donantes y a comunidades",
            "most_significant_change_technique": "fortalece la voz comunitaria en la evaluación de resultados",
            "outcome_harvesting": "se ajusta a contextos con teorías de cambio emergentes",
            "developmental_evaluation": "acompaña intervenciones en contextos dinámicos y complejos"
        }
        key = method.get('methodology', '').replace(' ', '_').lower()
        return contextualizations.get(key, "se adapta bien a las características del contexto guatemalteco")
    
    def generate_bibliography(self, references_used: List[str]) -> str:
        bibliography = "\n## REFERENCIAS BIBLIOGRÁFICAS\n\n"
        all_citations: List[str] = []
        for category in ["international_frameworks", "development_theories", "methodological_approaches", "evaluation_methods"]:
            for ref in self.reference_database.get(category, {}).values():
                if isinstance(ref, dict) and ref.get('citation'):
                    all_citations.append(ref['citation'])
        for category in ["national_statistics", "academic_institutions", "international_presence", "sector_specific"]:
            sources = self.guatemala_data_sources.get(category, {})
            for source in sources.values():
                if isinstance(source, dict) and source.get('citation'):
                    all_citations.append(source['citation'])
                elif isinstance(source, dict):
                    for subsource in source.values():
                        if isinstance(subsource, dict) and subsource.get('citation'):
                            all_citations.append(subsource['citation'])
        unique_citations = sorted(set(all_citations))
        for citation in unique_citations:
            bibliography += f"• {citation}\n\n"
        return bibliography
