import json
import os
from typing import Dict, List, Optional, Union
from pathlib import Path


class WebSearchTool:
    """
    Classe per gestire la configurazione del web search tool di Anthropic.
    
    Carica configurazioni da file JSON e genera schemi per il web search tool
    basati sulla documentazione ufficiale Anthropic.
    """
    
    # Modelli supportati dalla documentazione ufficiale
    SUPPORTED_MODELS = [
        "claude-3-7-sonnet-20250219",
        "claude-3-5-sonnet-latest", 
        "claude-3-5-haiku-latest"
    ]
    
    # Schema version dalla documentazione
    SCHEMA_VERSION = "web_search_20250305"
    
    # Pricing dalla documentazione ufficiale
    PRICING_INFO = {
        "cost_per_1000_searches": 10.00,
        "currency": "USD",
        "additional_costs": "Standard token costs for search-generated content",
        "billing_note": "Each web search counts as one use, regardless of results returned",
        "error_billing": "No billing for failed searches"
    }
    
    def __init__(
        self,
        config_dir: str = "tools/web_search_tool",
        allowed_domains_file: str = "allowed_domains.json",
        blocked_domains_file: str = "blocked_domains.json", 
        localizations_file: str = "localizations.json",
        auto_create_config_dir: bool = True
    ):
        """
        Inizializza la configurazione del web search tool.
        
        Args:
            config_dir (str): Directory dei file di configurazione
            allowed_domains_file (str): Nome del file con domini consentiti
            blocked_domains_file (str): Nome del file con domini bloccati
            localizations_file (str): Nome del file con le localizzazioni
            auto_create_config_dir (bool): Crea automaticamente la directory se non esiste
        """
        self.config_dir = Path(config_dir)
        self.allowed_domains_file = allowed_domains_file
        self.blocked_domains_file = blocked_domains_file
        self.localizations_file = localizations_file
        
        # Cache per i dati caricati
        self._allowed_domains_cache = None
        self._blocked_domains_cache = None
        self._localizations_cache = None
        
        # Crea directory se richiesto
        if auto_create_config_dir:
            self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_json_config(self, filename: str) -> Union[List, Dict]:
        """
        Carica un file JSON di configurazione.
        
        Args:
            filename (str): Nome del file JSON
            
        Returns:
            Union[List, Dict]: Contenuto del file JSON
            
        Raises:
            FileNotFoundError: Se il file non esiste
            json.JSONDecodeError: Se il file non è un JSON valido
        """
        file_path = self.config_dir / filename
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"File di configurazione non trovato: {file_path}\n"
                f"Assicurati che il file esista nella directory: {self.config_dir}"
            )
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Errore nel parsing JSON del file {file_path}: {e.msg}",
                e.doc, e.pos
            )
    
    @property
    def allowed_domains(self) -> List[str]:
        """Carica e restituisce la lista dei domini consentiti (con cache)."""
        if self._allowed_domains_cache is None:
            self._allowed_domains_cache = self._load_json_config(self.allowed_domains_file)
        return self._allowed_domains_cache
    
    @property
    def blocked_domains(self) -> List[str]:
        """Carica e restituisce la lista dei domini bloccati (con cache)."""
        if self._blocked_domains_cache is None:
            self._blocked_domains_cache = self._load_json_config(self.blocked_domains_file)
        return self._blocked_domains_cache
    
    @property
    def localizations(self) -> List[Dict]:
        """Carica e restituisce la lista delle localizzazioni (con cache)."""
        if self._localizations_cache is None:
            self._localizations_cache = self._load_json_config(self.localizations_file)
        return self._localizations_cache
    
    def clear_cache(self) -> None:
        """Pulisce la cache dei file caricati per forzare il ricaricamento."""
        self._allowed_domains_cache = None
        self._blocked_domains_cache = None
        self._localizations_cache = None
    
    def validate_model(self, model: str) -> bool:
        """
        Valida se il modello è supportato per il web search.
        
        Args:
            model (str): Nome del modello Claude
            
        Returns:
            bool: True se supportato
        """
        return any(
            model.startswith('-'.join(supported.split('-')[0:3])) 
            for supported in self.SUPPORTED_MODELS
        )
    
    def find_localization(self, location_name: str) -> Optional[Dict]:
        """
        Trova una localizzazione per nome (case-insensitive).
        
        Args:
            location_name (str): Nome della località
            
        Returns:
            Optional[Dict]: Configurazione della località o None se non trovata
        """
        return next(
            (loc for loc in self.localizations 
             if loc["name"].lower() == location_name.lower()),
            None
        )
    
    def get_available_locations(self) -> List[Dict]:
        """
        Restituisce informazioni riassuntive sulle località disponibili.
        
        Returns:
            List[Dict]: Lista con nome, valore strategico e timezone
        """
        return [
            {
                "name": loc["name"],
                "strategic_value": loc.get("strategic_value", "N/A"),
                "timezone": loc["timezone"],
                "country": loc["country"]
            }
            for loc in self.localizations
        ]
    
    def create_user_location_config(self, location_name: str) -> Dict:
        """
        Crea la configurazione user_location per una località specifica.
        
        Args:
            location_name (str): Nome della località
            
        Returns:
            Dict: Configurazione user_location
            
        Raises:
            ValueError: Se la località non è trovata
        """
        location_config = self.find_localization(location_name)
        
        if not location_config:
            available = [loc["name"] for loc in self.localizations]
            raise ValueError(
                f"Località non trovata: {location_name}. "
                f"Località disponibili: {', '.join(available)}"
            )
        
        return {
            "type": location_config["type"],
            "city": location_config["city"],
            "region": location_config["region"], 
            "country": location_config["country"],
            "timezone": location_config["timezone"]
        }
    
    def get_pricing_info(self) -> Dict:
        """Restituisce informazioni sui prezzi del web search tool."""
        return self.PRICING_INFO.copy()
    
    def get_supported_models(self) -> List[str]:
        """Restituisce la lista dei modelli supportati."""
        return self.SUPPORTED_MODELS.copy()
    
    def export_config_summary(self) -> Dict:
        """
        Esporta un riassunto completo della configurazione.
        
        Returns:
            Dict: Riassunto con statistiche e informazioni
        """
        return {
            "config_directory": str(self.config_dir),
            "files": {
                "allowed_domains": self.allowed_domains_file,
                "blocked_domains": self.blocked_domains_file,
                "localizations": self.localizations_file
            },
            "statistics": {
                "allowed_domains_count": len(self.allowed_domains),
                "blocked_domains_count": len(self.blocked_domains),
                "localizations_count": len(self.localizations)
            },
            "supported_models": self.SUPPORTED_MODELS,
            "schema_version": self.SCHEMA_VERSION,
            "pricing": self.PRICING_INFO
        }
        
    def get_web_search_schema(
        self,
        model: str,
        max_uses: int = 5,
        use_allowed_domains: bool = True,
        use_blocked_domains: bool = False,
        user_location: Optional[str] = None
    ) -> Dict:
        """
        Genera lo schema completo per il web search tool.
        
        Args:
            model (str): Nome del modello Claude
            max_uses (int): Numero massimo di ricerche (default: 5)
            use_allowed_domains (bool): Se usare la whitelist dei domini
            use_blocked_domains (bool): Se usare la blacklist dei domini
            user_location (str): Nome della località per la localizzazione
            
        Returns:
            Dict: Schema completo del web search tool
            
        Raises:
            ValueError: Se ci sono errori di validazione
        """
        # Validazione modello
        if not self.validate_model(model):
            raise ValueError(
                f"Modello non supportato per web search: {model}. "
                f"Modelli supportati: {', '.join(self.SUPPORTED_MODELS)}. "
                f"Vedi: https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/web-search-tool"
            )
        
        # Validazione mutually exclusive domains
        if use_allowed_domains and use_blocked_domains:
            raise ValueError(
                "Non puoi usare sia allowed_domains che blocked_domains nello stesso request. "
                "Scegli uno dei due filtri."
            )
        
        # Costruzione schema base
        schema = {
            "type": self.SCHEMA_VERSION,
            "name": "web_search",
            "max_uses": max_uses
        }
        
        # Aggiunta filtri domini (mutually exclusive)
        if use_allowed_domains:
            domains = self.allowed_domains
            if domains:
                schema["allowed_domains"] = domains
        elif use_blocked_domains:
            domains = self.blocked_domains
            if domains:
                schema["blocked_domains"] = domains
        
        # Aggiunta localizzazione se specificata
        if user_location:
            schema["user_location"] = self.create_user_location_config(user_location)
        
        return schema
    