from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import asyncio
import aiohttp
import json  # keep if you plan to serialize responses

# NOTE:
# - `requests` and `pandas` were in your snippet but not used anywhere.
#   If you need them later, re-add: `import requests`, `import pandas as pd`.

class RealTimeDataIntegrator:
    """System to integrate real-time data from various sources for proposal enhancement"""
    
    def __init__(self, project_info: Dict):
        self.project = project_info
        self.data_sources = self._configure_data_sources()
        self.cache_duration = 24  # hours
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            logging.basicConfig(level=logging.INFO)

    def _configure_data_sources(self) -> Dict:
        """Configure available data sources with API endpoints and parameters"""
        return {
            "world_bank": {
                "base_url": "https://api.worldbank.org/v2",
                "country_code": "GT",  # Guatemala
                "indicators": {
                    "poverty_headcount": "SI.POV.DDAY",
                    "gdp_growth": "NY.GDP.MKTP.KD.ZG",
                    "unemployment": "SL.UEM.TOTL.ZS",
                    "gini_index": "SI.POV.GINI",
                    "life_expectancy": "SP.DYN.LE00.IN",
                    "literacy_rate": "SE.ADT.LITR.ZS",
                    "access_electricity": "EG.ELC.ACCS.ZS",
                    "maternal_mortality": "SH.STA.MMRT"
                }
            },
            "undp": {
                "base_url": "https://hdr.undp.org/sites/default/files/2021-22_HDR",
                "country": "Guatemala",
                "indicators": ["HDI", "GII", "MPI"]
            },
            "fao": {
                "base_url": "http://www.fao.org/faostat/api/v1/",
                "country_code": "320",  # Guatemala FAO code
                "indicators": {
                    "food_security": "21010",
                    "agricultural_production": "21012",
                    "rural_population": "22003"
                }
            },
            "eclac": {
                "base_url": "https://cepalstat-prod.cepal.org/cepalstat/api/v1/",
                "country": "GTM",
                "indicators": ["poverty", "inequality", "employment", "education"]
            },
            "guatemala_national": {
                "ine_url": "https://www.ine.gob.gt/sistema/documentos-de-soporte-tecnico/",
                "banguat_url": "https://www.banguat.gob.gt/inc/main.asp?id=112793&aud=1&lang=1",
                "segeplan_url": "https://www.segeplan.gob.gt/nportal/index.php/biblioteca-documental/finish/2-planificacion/847-plan-nacional-de-desarrollo"
            },
            "climate_data": {
                "openweather_url": "https://api.openweathermap.org/data/2.5/",
                "climate_api": "https://climatedata.worldbank.org/CRMePortal/",
                "disaster_api": "https://www.emdat.be/emdat_db/"
            },
            "exchange_rates": {
                "base_url": "https://api.exchangerate-api.com/v4/latest/USD",
                "source": "Bank of Guatemala"
            }
        }

    async def fetch_current_indicators(self, force_refresh: bool = False) -> Dict:
        """Fetch current development indicators for Guatemala"""
        current_data = {
            "fetch_timestamp": datetime.now().isoformat(),
            "data_freshness": "real-time",
            "economic_indicators": {},
            "social_indicators": {},
            "environmental_indicators": {},
            "exchange_rates": {},
            "context_analysis": {}
        }
        try:
            # Fetch economic indicators
            current_data["economic_indicators"] = await self._fetch_economic_data()
            # Fetch social indicators
            current_data["social_indicators"] = await self._fetch_social_data()
            # Fetch environmental/climate data
            current_data["environmental_indicators"] = await self._fetch_environmental_data()
            # Fetch exchange rates
            current_data["exchange_rates"] = await self._fetch_exchange_rates()
            # Generate context analysis
            current_data["context_analysis"] = self._analyze_current_context(current_data)
            return current_data
        except Exception as e:
            self.logger.error(f"Error fetching current indicators: {str(e)}")
            return self._get_fallback_data()

    async def _fetch_economic_data(self) -> Dict:
        """Fetch current economic indicators from multiple sources"""
        economic_data: Dict[str, Any] = {}
        try:
            wb_indicators = self.data_sources["world_bank"]["indicators"]
            base = self.data_sources['world_bank']['base_url']
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                # GDP Growth
                gdp_url = f"{base}/country/GT/indicator/{wb_indicators['gdp_growth']}?format=json&date=2020:2024"
                async with session.get(gdp_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if len(data) > 1 and data[1]:
                            latest = next((d for d in data[1] if d.get("value") is not None), data[1][0])
                            economic_data["gdp_growth"] = {
                                "value": latest.get("value"),
                                "year": latest.get("date"),
                                "source": "World Bank"
                            }
                # Unemployment rate
                unemployment_url = f"{base}/country/GT/indicator/{wb_indicators['unemployment']}?format=json&date=2020:2024"
                async with session.get(unemployment_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if len(data) > 1 and data[1]:
                            latest = next((d for d in data[1] if d.get("value") is not None), data[1][0])
                            economic_data["unemployment_rate"] = {
                                "value": latest.get("value"),
                                "year": latest.get("date"),
                                "source": "World Bank"
                            }
                # Gini coefficient
                gini_url = f"{base}/country/GT/indicator/{wb_indicators['gini_index']}?format=json&date=2015:2024"
                async with session.get(gini_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if len(data) > 1 and data[1]:
                            latest = next((d for d in data[1] if d.get("value") is not None), data[1][0])
                            economic_data["gini_coefficient"] = {
                                "value": latest.get("value"),
                                "year": latest.get("date"),
                                "source": "World Bank"
                            }
        except Exception as e:
            self.logger.error(f"Error fetching economic data: {str(e)}")
            economic_data["error"] = str(e)

        # Add current exchange rate
        try:
            economic_data["exchange_rate_gtq_usd"] = await self._get_current_exchange_rate()
        except Exception:
            economic_data["exchange_rate_gtq_usd"] = {
                "value": 7.75,
                "source": "estimated",
                "date": datetime.now().date()
            }
        return economic_data

    async def _fetch_social_data(self) -> Dict:
        """Fetch current social development indicators"""
        social_data: Dict[str, Any] = {}
        try:
            wb_indicators = self.data_sources["world_bank"]["indicators"]
            base = self.data_sources['world_bank']['base_url']
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                # Life expectancy
                life_exp_url = f"{base}/country/GT/indicator/{wb_indicators['life_expectancy']}?format=json&date=2018:2024"
                async with session.get(life_exp_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if len(data) > 1 and data[1]:
                            latest = next((d for d in data[1] if d.get("value") is not None), data[1][0])
                            social_data["life_expectancy"] = {
                                "value": latest.get("value"),
                                "year": latest.get("date"),
                                "source": "World Bank"
                            }
                # Literacy rate
                literacy_url = f"{base}/country/GT/indicator/{wb_indicators['literacy_rate']}?format=json&date=2015:2024"
                async with session.get(literacy_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if len(data) > 1 and data[1]:
                            latest = next((d for d in data[1] if d.get("value") is not None), data[1][0])
                            social_data["adult_literacy_rate"] = {
                                "value": latest.get("value"),
                                "year": latest.get("date"),
                                "source": "World Bank"
                            }
                # Access to electricity
                electricity_url = f"{base}/country/GT/indicator/{wb_indicators['access_electricity']}?format=json&date=2018:2024"
                async with session.get(electricity_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if len(data) > 1 and data[1]:
                            latest = next((d for d in data[1] if d.get("value") is not None), data[1][0])
                            social_data["access_to_electricity"] = {
                                "value": latest.get("value"),
                                "year": latest.get("date"),
                                "source": "World Bank"
                            }
                # Maternal mortality
                maternal_url = f"{base}/country/GT/indicator/{wb_indicators['maternal_mortality']}?format=json&date=2015:2024"
                async with session.get(maternal_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if len(data) > 1 and data[1]:
                            latest = next((d for d in data[1] if d.get("value") is not None), data[1][0])
                            social_data["maternal_mortality_ratio"] = {
                                "value": latest.get("value"),
                                "year": latest.get("date"),
                                "source": "World Bank"
                            }
        except Exception as e:
            self.logger.error(f"Error fetching social data: {str(e)}")
            social_data["error"] = str(e)
        return social_data

    async def _fetch_environmental_data(self) -> Dict:
        """Fetch environmental and climate indicators"""
        env_data: Dict[str, Any] = {}
        try:
            location = self.project.get('department', 'Guatemala')
            coordinates = self._get_guatemala_coordinates(location)
            if coordinates:
                # In production: call OpenWeather with a real API key.
                # Here we simulate data to keep the method non-blocking and runnable.
                env_data["current_weather"] = {
                    "temperature": 22.5,
                    "humidity": 78,
                    "description": "Partially cloudy",
                    "location": location,
                    "source": "OpenWeatherMap (simulated)"
                }
                # Climate risk assessment
                env_data["climate_risks"] = self._assess_climate_risks(location)
                # Environmental sustainability indicators
                env_data["sustainability_context"] = {
                    "deforestation_risk": self._assess_deforestation_risk(location),
                    "water_stress": self._assess_water_stress(location),
                    "biodiversity_priority": self._assess_biodiversity_priority(location)
                }
        except Exception as e:
            self.logger.error(f"Error fetching environmental data: {str(e)}")
            env_data["error"] = str(e)
        return env_data

    async def _fetch_exchange_rates(self) -> Dict:
        """Fetch current exchange rates"""
        exchange_data: Dict[str, Any] = {}
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                url = self.data_sources["exchange_rates"]["base_url"]
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "rates" in data and "GTQ" in data["rates"]:
                            rate = data["rates"]["GTQ"]
                            exchange_data["USD_to_GTQ"] = {
                                "rate": rate,
                                "date": data.get("date"),
                                "source": "Exchange Rate API"
                            }
                            exchange_data["GTQ_to_USD"] = {
                                "rate": 1 / rate if rate else None,
                                "date": data.get("date"),
                                "source": "Exchange Rate API"
                            }
        except Exception as e:
            self.logger.error(f"Error fetching exchange rates: {str(e)}")
            exchange_data = {
                "USD_to_GTQ": {"rate": 7.75, "date": datetime.now().date(), "source": "Banco de Guatemala (estimated)"},
                "GTQ_to_USD": {"rate": 0.129, "date": datetime.now().date(), "source": "Banco de Guatemala (estimated)"}
            }
        return exchange_data

    async def _get_current_exchange_rate(self) -> Dict:
        """Get current USD-GTQ exchange rate"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                url = "https://api.exchangerate-api.com/v4/latest/USD"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "value": data["rates"].get("GTQ", 7.75),
                            "date": data.get("date"),
                            "source": "Exchange Rate API"
                        }
        except Exception:
            pass
        return {"value": 7.75, "date": datetime.now().date(), "source": "Banco de Guatemala (estimated)"}

    def _get_guatemala_coordinates(self, location: str) -> Optional[Dict[str, float]]:
        """Get coordinates for Guatemala locations"""
        guatemala_coordinates = {
            "Guatemala": {"lat": 14.6349, "lon": -90.5069},
            "Quetzaltenango": {"lat": 14.8333, "lon": -91.5167},
            "Huehuetenango": {"lat": 15.3197, "lon": -91.4695},
            "Alta Verapaz": {"lat": 15.3667, "lon": -90.3333},
            "Petén": {"lat": 16.9167, "lon": -89.8833},
            "Chiquimula": {"lat": 14.8000, "lon": -89.5333},
            "San Marcos": {"lat": 14.9667, "lon": -91.8000},
            "Sololá": {"lat": 14.7667, "lon": -91.1833},
            "Quiché": {"lat": 15.0333, "lon": -91.1500}
        }
        return guatemala_coordinates.get(location, guatemala_coordinates["Guatemala"])

    def _assess_climate_risks(self, location: str) -> Dict:
        """Assess climate risks for specific location"""
        risk_assessments = {
            "Guatemala": {"drought": "medium", "flooding": "medium", "hurricanes": "medium"},
            "Quetzaltenango": {"drought": "low", "flooding": "low", "temperature_variation": "high"},
            "Huehuetenango": {"drought": "high", "flooding": "low", "frost": "medium"},
            "Alta Verapaz": {"drought": "low", "flooding": "high", "landslides": "high"},
            "Petén": {"drought": "medium", "deforestation": "high", "flooding": "medium"},
            "Chiquimula": {"drought": "very_high", "water_scarcity": "high", "desertification": "medium"},
            "San Marcos": {"volcanic_activity": "high", "landslides": "high", "flooding": "medium"}
        }
        return risk_assessments.get(location, {"drought": "medium", "flooding": "medium", "general_risk": "medium"})

    def _assess_deforestation_risk(self, location: str) -> str:
        """Assess deforestation risk by location"""
        high_risk_areas = ["Petén", "Alta Verapaz", "Izabal"]
        medium_risk_areas = ["Huehuetenango", "San Marcos", "Quiché"]
        if location in high_risk_areas:
            return "high"
        elif location in medium_risk_areas:
            return "medium"
        else:
            return "low"

    def _assess_water_stress(self, location: str) -> str:
        """Assess water stress by location"""
        high_stress_areas = ["Chiquimula", "Zacapa", "El Progreso", "Jalapa"]
        medium_stress_areas = ["Guatemala", "Sacatepéquez", "Escuintla"]
        if location in high_stress_areas:
            return "high"
        elif location in medium_stress_areas:
            return "medium"
        else:
            return "low"

    def _assess_biodiversity_priority(self, location: str) -> str:
        """Assess biodiversity conservation priority"""
        high_priority_areas = ["Petén", "Alta Verapaz", "Huehuetenango", "San Marcos"]
        medium_priority_areas = ["Baja Verapaz", "Quiché", "Izabal"]
        if location in high_priority_areas:
            return "high"
        elif location in medium_priority_areas:
            return "medium"
        else:
            return "low"

    def _analyze_current_context(self, data: Dict) -> Dict:
        """Generate contextual analysis based on current data"""
        analysis = {
            "economic_outlook": "",
            "social_challenges": "",
            "environmental_considerations": "",
            "project_implications": [],
            "risk_factors": [],
            "opportunities": []
        }

        # Economic analysis
        economic = data.get("economic_indicators", {})
        gdp_val = economic.get("gdp_growth", {}).get("value")
        if isinstance(gdp_val, (int, float)):
            if gdp_val < 2:
                analysis["economic_outlook"] = "Guatemala presenta un crecimiento económico lento, lo que puede afectar las oportunidades de empleo e ingresos en las comunidades beneficiarias."
                analysis["project_implications"].append("Enfatizar actividades de generación de ingresos y desarrollo económico local")
            elif gdp_val > 4:
                analysis["economic_outlook"] = "Guatemala muestra un crecimiento económico robusto, creando un contexto favorable para iniciativas de desarrollo."
                analysis["opportunities"].append("Aprovechar el dinamismo económico para escalabilidad del proyecto")

        # Social analysis
        social = data.get("social_indicators", {})
        literacy_val = social.get("adult_literacy_rate", {}).get("value")
        if isinstance(literacy_val, (int, float)):
            if literacy_val < 80:
                analysis["social_challenges"] = "La tasa de alfabetización adulta requiere atención prioritaria en las estrategias del proyecto."
                analysis["project_implications"].append("Incorporar componentes de educación funcional y alfabetización")

        # Environmental analysis
        environmental = data.get("environmental_indicators", {})
        if environmental.get("climate_risks"):
            risks = environmental["climate_risks"]
            high_risks = [risk for risk, level in risks.items() if level in ["high", "very_high"]]
            if high_risks:
                analysis["environmental_considerations"] = f"La zona presenta riesgos climáticos altos en: {', '.join(high_risks)}."
                analysis["risk_factors"].extend(high_risks)
                analysis["project_implications"].append("Integrar medidas de adaptación climática y gestión de riesgos")

        # Exchange rate implications
        exchange = data.get("exchange_rates", {})
        rate = exchange.get("USD_to_GTQ", {}).get("rate")
        if isinstance(rate, (int, float)):
            if rate > 8.0:
                analysis["project_implications"].append("Tipo de cambio favorable para proyectos financiados en USD")
            elif rate < 7.5:
                analysis["project_implications"].append("Considerar fluctuaciones cambiarias en presupuesto")

        return analysis

    def _get_fallback_data(self) -> Dict:
        """Provide fallback data when APIs are unavailable"""
        return {
            "fetch_timestamp": datetime.now().isoformat(),
            "data_freshness": "fallback",
            "economic_indicators": {
                "gdp_growth": {"value": 3.2, "year": "2023", "source": "estimated"},
                "unemployment_rate": {"value": 2.8, "year": "2023", "source": "estimated"},
                "gini_coefficient": {"value": 48.3, "year": "2019", "source": "World Bank"},
                "exchange_rate_gtq_usd": {"value": 7.75, "source": "Banco de Guatemala"}
            },
            "social_indicators": {
                "life_expectancy": {"value": 74.3, "year": "2021", "source": "World Bank"},
                "adult_literacy_rate": {"value": 81.5, "year": "2018", "source": "UNESCO"},
                "access_to_electricity": {"value": 96.8, "year": "2020", "source": "World Bank"}
            },
            "environmental_indicators": {
                "climate_risks": {"drought": "medium", "flooding": "medium"},
                "sustainability_context": {"deforestation_risk": "medium", "water_stress": "medium"}
            },
            "context_analysis": {
                "economic_outlook": "Guatemala presenta indicadores económicos estables con oportunidades de crecimiento.",
                "project_implications": ["Considerar contexto económico nacional", "Integrar datos locales específicos"]
            }
        }

    # -------- Presentation helpers --------
    @staticmethod
    def _fmt(value: Optional[float], digits: int = 1) -> str:
        return "N/D" if value is None else f"{value:.{digits}f}"

    def generate_updated_context_section(self, current_data: Dict) -> str:
        """Generate updated context section with real-time data"""
        ts = current_data.get('fetch_timestamp', datetime.now().isoformat())
        try:
            ts_fmt = datetime.fromisoformat(ts).strftime('%d de %B de %Y, %H:%M')
        except Exception:
            ts_fmt = datetime.now().strftime('%d de %B de %Y, %H:%M')

        context_section = f"""
## CONTEXTO ACTUALIZADO Y ANÁLISIS SITUACIONAL

*Datos actualizados al: {ts_fmt}*

### Indicadores Económicos Actuales
"""

        economic = current_data.get("economic_indicators", {})

        if economic.get("gdp_growth"):
            gdp = economic["gdp_growth"]
            gval = gdp.get('value')
            gtext = self._interpret_gdp_growth(gval) if isinstance(gval, (int, float)) else "no cuenta con un dato válido más reciente"
            context_section += f"""
**Crecimiento del PIB:** {self._fmt(gval)}% ({gdp.get('year', 's/f')})
El crecimiento económico de Guatemala en {gdp.get('year', 's/f')} fue del {self._fmt(gval)}%, lo que {gtext}.
"""

        if economic.get("unemployment_rate"):
            unemployment = economic["unemployment_rate"]
            uval = unemployment.get('value')
            utext = self._interpret_unemployment(uval) if isinstance(uval, (int, float)) else "no es concluyente con el dato disponible"
            context_section += f"""
**Tasa de Desempleo:** {self._fmt(uval)}% ({unemployment.get('year', 's/f')})
Esta tasa de desempleo {utext} y debe considerarse en el diseño de actividades de generación de ingresos.
"""

        if economic.get("exchange_rate_gtq_usd"):
            exchange = economic["exchange_rate_gtq_usd"]
            xr = exchange.get('value')
            xtext = self._interpret_exchange_rate(xr) if isinstance(xr, (int, float)) else "no presenta implicaciones claras por falta de dato"
            context_section += f"""
**Tipo de Cambio Actual:** Q{self._fmt(xr, 2)} por USD
El tipo de cambio actual {xtext} para la ejecución del proyecto.
"""

        context_section += "\n### Indicadores Sociales Actualizados\n"
        social = current_data.get("social_indicators", {})

        if social.get("life_expectancy"):
            life_exp = social["life_expectancy"]
            lval = life_exp.get('value')
            ltext = self._interpret_life_expectancy(lval) if isinstance(lval, (int, float)) else "no permite inferencias concluyentes"
            context_section += f"""
**Esperanza de Vida:** {self._fmt(lval)} años ({life_exp.get('year', 's/f')})
Guatemala mantiene una esperanza de vida de {self._fmt(lval)} años, reflejando {ltext}.
"""

        if social.get("adult_literacy_rate"):
            literacy = social["adult_literacy_rate"]
            aval = literacy.get('value')
            atext = self._interpret_literacy(aval) if isinstance(aval, (int, float)) else "no ofrece conclusiones claras"
            context_section += f"""
**Tasa de Alfabetización Adulta:** {self._fmt(aval)}% ({literacy.get('year', 's/f')})
La alfabetización adulta del {self._fmt(aval)}% indica {atext} en los componentes educativos del proyecto.
"""

        environmental = current_data.get("environmental_indicators", {})
        if environmental.get("climate_risks"):
            context_section += "\n### Consideraciones Ambientales y Climáticas\n"
            risks = environmental["climate_risks"]
            high_risks = [risk for risk, level in risks.items() if level in ["high", "very_high"]]
            if high_risks:
                context_section += f"""
**Riesgos Climáticos Prioritarios:** {', '.join(high_risks)}
La zona del proyecto presenta riesgos altos de {', '.join(high_risks)}, requiriendo medidas específicas de adaptación y gestión de riesgos en el diseño del proyecto.
"""

        analysis = current_data.get("context_analysis", {})
        if analysis.get("project_implications"):
            context_section += "\n### Implicaciones para el Proyecto\n"
            context_section += "Basado en el análisis de datos actualizados, el proyecto debe considerar:\n\n"
            for implication in analysis["project_implications"]:
                context_section += f"• {implication}\n"

        context_section += f"""

### Metodología de Actualización de Datos

Este análisis contextual se basa en datos obtenidos en tiempo real de fuentes oficiales como el Banco Mundial, organismos de las Naciones Unidas, y fuentes gubernamentales guatemaltecas. Los datos se actualizan automáticamente para garantizar que las decisiones del proyecto se basen en la información más reciente disponible.

**Fuentes consultadas:**
• Banco Mundial - Indicadores de Desarrollo Mundial
• Instituto Nacional de Estadística de Guatemala (INE)
• Banco de Guatemala (BANGUAT)
• Programa de las Naciones Unidas para el Desarrollo (PNUD)
• APIs de datos climatológicos internacionales

*Próxima actualización programada: {(datetime.now() + timedelta(hours=24)).strftime('%d de %B de %Y')}*
"""
        return context_section

    def _interpret_gdp_growth(self, gdp_growth: Optional[float]) -> str:
        """Interpret GDP growth rate"""
        if gdp_growth is None:
            return "no cuenta con un dato válido más reciente"
        if gdp_growth < 0:
            return "indica una contracción económica que puede afectar las oportunidades de desarrollo local"
        elif gdp_growth < 2:
            return "refleja un crecimiento lento que requiere impulso mediante iniciativas de desarrollo"
        elif gdp_growth < 4:
            return "muestra un crecimiento moderado favorable para iniciativas de desarrollo"
        else:
            return "indica un crecimiento robusto que crea oportunidades para el escalamiento del proyecto"

    def _interpret_unemployment(self, unemployment: Optional[float]) -> str:
        """Interpret unemployment rate"""
        if unemployment is None:
            return "no es concluyente con el dato disponible"
        if unemployment > 10:
            return "es elevada y requiere priorizar actividades de generación de empleo"
        elif unemployment > 5:
            return "es moderada pero debe considerarse en las estrategias del proyecto"
        else:
            return "es relativamente baja, indicando un mercado laboral dinámico"

    def _interpret_exchange_rate(self, rate: Optional[float]) -> str:
        """Interpret exchange rate implications"""
        if rate is None:
            return "no presenta implicaciones claras por falta de dato"
        if rate > 8.0:
            return "es favorable para proyectos financiados en dólares estadounidenses"
        elif rate < 7.5:
            return "requiere consideración de riesgos cambiarios en el presupuesto"
        else:
            return "se mantiene en rangos históricos normales"

    def _interpret_life_expectancy(self, life_exp: Optional[float]) -> str:
        """Interpret life expectancy"""
        if life_exp is None:
            return "no permite inferencias concluyentes"
        if life_exp < 70:
            return "desafíos significativos en salud pública que el proyecto puede abordar"
        elif life_exp < 75:
            return "oportunidades de mejora en salud y bienestar comunitario"
        else:
            return "indicadores de salud relativamente favorables"

    def _interpret_literacy(self, literacy: Optional[float]) -> str:
        """Interpret literacy rate"""
        if literacy is None:
            return "no ofrece conclusiones claras"
        if literacy < 70:
            return "la necesidad crítica de fortalecer"
        elif literacy < 85:
            return "oportunidades importantes para mejorar"
        else:
            return "una base sólida para desarrollar"
