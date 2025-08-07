import shutil
import os
from typing import Optional, List

# Text edit schema per i 3 modelli stato dell'arte di Anthropic

def get_text_edit_schema(model):
    """
    Restituisce lo schema del text editor tool basato sul modello Claude.
    
    Dati dalla documentazione ufficiale Anthropic (agosto 2025):
    - Claude 4 (Opus & Sonnet): text_editor_20250429
    - Claude 3.7 Sonnet: text_editor_20250124  
    - Claude 3.5 Sonnet: text_editor_20241022
    
    Args:
        model (str): Nome del modello Claude
        
    Returns:
        dict: Schema del text editor tool
        
    Raises:
        ValueError: Se il modello non è supportato
    """
    
    # Claude 4 family (Opus & Sonnet) - rilasciato 29 aprile 2025
    # NOTA: Non include il comando undo_edit
    if model.startswith("claude-opus-4") or model.startswith("claude-sonnet-4"):
        return {
            "type": "text_editor_20250429",
            "name": "str_replace_based_edit_tool",  # Nome aggiornato dalla docs
        }
    
    # Claude 3.7 Sonnet - rilasciato 24 gennaio 2025
    # Include tutti i comandi compreso undo_edit
    elif model.startswith("claude-3-7-sonnet"):
        return {
            "type": "text_editor_20250124",
            "name": "str_replace_based_edit_tool",
        }
    
    # Claude 3.5 Sonnet - rilasciato 22 ottobre 2024  
    # Include tutti i comandi compreso undo_edit
    elif model.startswith("claude-3-5-sonnet"):
        return {
            "type": "text_editor_20241022", 
            "name": "str_replace_based_edit_tool",
        }
    
    else:
        supported_models = [
            "claude-opus-4-* (text_editor_20250429)",
            "claude-sonnet-4-* (text_editor_20250429)", 
            "claude-3-7-sonnet-* (text_editor_20250124)",
            "claude-3-5-sonnet-* (text_editor_20241022)"
        ]
        raise ValueError(
            f"Modello non supportato: {model}. "
            f"Modelli supportati: {', '.join(supported_models)}. "
            f"Vedi: https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/text-editor-tool"
        )


# TOOL CLASS
class TextEditorTool:
    """
    Gestisce operazioni di base su file di testo, tra cui lettura, modifica,
    creazione e inserimento di contenuto.
    
    Questa classe fornisce un'interfaccia sicura per manipolare file all'interno
    di una directory specificata, prevenendo l'accesso a percorsi al di fuori
    della directory di base. Include inoltre funzionalità di backup automatico
    per consentire l'annullamento delle modifiche.
    """
    def __init__(self, base_dir: str = "", backup_dir: str = ""):
        """
        Inizializza l'istanza della classe.
        
        Args:
            base_dir (str): La directory di base entro la quale tutte le
                            operazioni sui file sono consentite.
                            Se non specificata, viene usata la directory
                            corrente.
            backup_dir (str): La directory in cui verranno salvati i file di
                              backup. Se non specificata, viene creata una
                              sottodirectory chiamata '.backups' all'interno
                              della directory di base.
        """
        self.base_dir = base_dir or os.getcwd()
        self.backup_dir = backup_dir or os.path.join(self.base_dir, ".backups")
        os.makedirs(self.backup_dir, exist_ok=True)

    def _validate_path(self, file_path: str) -> str:
        """
        Verifica che il percorso del file sia all'interno della directory di base.
        
        Questo metodo previene attacchi di tipo "directory traversal" assicurando
        che l'utente non possa accedere a file al di fuori dell'area di lavoro
        predefinita. Solleva un errore se il percorso è non valido.
        
        Args:
            file_path (str): Il percorso del file da validare.
            
        Returns:
            str: Il percorso assoluto e normalizzato del file.
            
        Raises:
            ValueError: Se il percorso del file si trova al di fuori della
                        directory di base consentita.
        """
        abs_path = os.path.normpath(os.path.join(self.base_dir, file_path))
        if not abs_path.startswith(self.base_dir):
            raise ValueError(
                f"Access denied: Path '{file_path}' is outside the allowed directory"
            )
        return abs_path

    def _backup_file(self, file_path: str) -> str:
        """
        Crea una copia di backup di un file esistente.
        
        Il backup viene salvato nella directory di backup con un timestamp
        (basato sull'ultima modifica del file) per garantire nomi univoci.
        
        Args:
            file_path (str): Il percorso assoluto del file da salvare.
            
        Returns:
            str: Il percorso del file di backup creato, o una stringa vuota
                 se il file originale non esiste.
        """
        if not os.path.exists(file_path):
            return ""
        file_name = os.path.basename(file_path)
        backup_path = os.path.join(
            self.backup_dir, f"{file_name}.{os.path.getmtime(file_path):.0f}"
        )
        shutil.copy2(file_path, backup_path)
        return backup_path

    def _restore_backup(self, file_path: str) -> str:
        """
        Ripristina l'ultima versione di backup di un file.
        
        Cerca il file di backup più recente nella directory di backup e lo
        ripristina, sovrascrivendo il file originale.
        
        Args:
            file_path (str): Il percorso assoluto del file da ripristinare.
            
        Returns:
            str: Un messaggio di conferma del ripristino avvenuto con successo.
            
        Raises:
            FileNotFoundError: Se non viene trovato alcun file di backup
                               per il percorso specificato.
        """
        file_name = os.path.basename(file_path)
        backups = [
            f
            for f in os.listdir(self.backup_dir)
            if f.startswith(file_name + ".")
        ]
        if not backups:
            raise FileNotFoundError(f"No backups found for {file_path}")

        latest_backup = sorted(backups, reverse=True)[0]
        backup_path = os.path.join(self.backup_dir, latest_backup)

        shutil.copy2(backup_path, file_path)
        return f"Successfully restored {file_path} from backup"

    def _count_matches(self, content: str, old_str: str) -> int:
        """
        Conta il numero di occorrenze di una sottostringa all'interno di una stringa.
        
        Questo è un metodo di utilità interno per supportare la funzione
        `str_replace`, assicurando che la sostituzione avvenga in modo univoco.
        
        Args:
            content (str): La stringa principale in cui cercare.
            old_str (str): La sottostringa da contare.
            
        Returns:
            int: Il numero di occorrenze trovate.
        """
        return content.count(old_str)

    def view(
        self, file_path: str, view_range: Optional[List[int]] = None
    ) -> str:
        """
        Legge il contenuto di un file o elenca i contenuti di una directory.
        
        Se il percorso punta a un file, legge il contenuto e restituisce ogni
        riga numerata. Se viene fornito `view_range`, restituisce solo le righe
        comprese nell'intervallo specificato (le righe sono 1-based).
        Se il percorso è una directory, ne restituisce i contenuti.
        
        Args:
            file_path (str): Il percorso del file o della directory da visualizzare.
            view_range (Optional[List[int]]): Un intervallo di righe da
                                              visualizzare (es. [1, 10]).
                                              Se `None`, visualizza l'intero file.
                                              Se l'end è -1, visualizza fino
                                              alla fine del file.
        
        Returns:
            str: Il contenuto del file formattato con i numeri di riga, o
                 l'elenco dei contenuti della directory.
                 
        Raises:
            FileNotFoundError: Se il file o la directory non esiste.
            PermissionError: Se i permessi di lettura sono negati.
            UnicodeDecodeError: Se il file non è un file di testo valido.
        """
        try:
            abs_path = self._validate_path(file_path)

            if os.path.isdir(abs_path):
                try:
                    return "\n".join(os.listdir(abs_path))
                except PermissionError:
                    raise PermissionError(
                        "Permission denied. Cannot list directory contents."
                    )

            if not os.path.exists(abs_path):
                raise FileNotFoundError("File not found")

            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read()

            if view_range:
                start, end = view_range
                lines = content.split("\n")

                if end == -1:
                    end = len(lines)

                selected_lines = lines[start - 1 : end]

                result = []
                for i, line in enumerate(selected_lines, start):
                    result.append(f"{i}: {line}")

                return "\n".join(result)
            else:
                lines = content.split("\n")
                result = []
                for i, line in enumerate(lines, 1):
                    result.append(f"{i}: {line}")

                return "\n".join(result)

        except UnicodeDecodeError:
            raise UnicodeDecodeError(
                "utf-8",
                b"",
                0,
                1,
                "File contains non-text content and cannot be displayed.",
            )
        except ValueError as e:
            raise ValueError(str(e))
        except PermissionError:
            raise PermissionError("Permission denied. Cannot access file.")
        except Exception as e:
            raise type(e)(str(e))

    def str_replace(self, file_path: str, old_str: str, new_str: str) -> str:
        """
        Sostituisce un'esatta e unica occorrenza di una stringa in un file.
        
        Prima di eseguire la sostituzione, il metodo crea un backup del file.
        Il metodo è progettato per operare solo se la stringa da sostituire
        `old_str` compare esattamente una volta nel file. Questo previene
        sostituzioni involontarie e non desiderate.
        
        Args:
            file_path (str): Il percorso del file da modificare.
            old_str (str): La stringa da cercare e sostituire.
            new_str (str): La nuova stringa con cui sostituire.
            
        Returns:
            str: Un messaggio di successo che indica l'avvenuta sostituzione.
            
        Raises:
            FileNotFoundError: Se il file non esiste.
            ValueError: Se non viene trovata alcuna corrispondenza o se ne
                        vengono trovate più di una.
            PermissionError: Se i permessi di scrittura sono negati.
        """
        try:
            abs_path = self._validate_path(file_path)

            if not os.path.exists(abs_path):
                raise FileNotFoundError("File not found")

            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read()

            match_count = self._count_matches(content, old_str)

            if match_count == 0:
                raise ValueError(
                    "No match found for replacement. Please check your text and try again."
                )
            elif match_count > 1:
                raise ValueError(
                    f"Found {match_count} matches for replacement text. Please provide more context to make a unique match."
                )

            # Create backup before modifying
            self._backup_file(abs_path)

            # Perform the replacement
            new_content = content.replace(old_str, new_str)

            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return "Successfully replaced text at exactly one location."

        except ValueError as e:
            raise ValueError(str(e))
        except PermissionError:
            raise PermissionError("Permission denied. Cannot modify file.")
        except Exception as e:
            raise type(e)(str(e))

    def create(self, file_path: str, file_text: str) -> str:
        """
        Crea un nuovo file con il contenuto specificato.
        
        Il metodo verifica prima se il file esiste già per evitare sovrascritture
        accidentali. Crea anche le directory padre se non esistono.
        
        Args:
            file_path (str): Il percorso del nuovo file da creare.
            file_text (str): Il contenuto testuale da scrivere nel file.
            
        Returns:
            str: Un messaggio di successo che indica la creazione del file.
            
        Raises:
            FileExistsError: Se il file esiste già.
            PermissionError: Se i permessi di scrittura sono negati.
        """
        try:
            abs_path = self._validate_path(file_path)

            # Check if file already exists
            if os.path.exists(abs_path):
                raise FileExistsError(
                    "File already exists. Use str_replace to modify it."
                )

            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            # Create the file
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(file_text)

            return f"Successfully created {file_path}"

        except ValueError as e:
            raise ValueError(str(e))
        except PermissionError:
            raise PermissionError("Permission denied. Cannot create file.")
        except Exception as e:
            raise type(e)(str(e))

    def insert(self, file_path: str, insert_line: int, new_str: str) -> str:
        """
        Inserisce una nuova riga di testo in una posizione specifica di un file.
        
        Prima di inserire il testo, il metodo crea un backup del file.
        Il testo viene inserito dopo la riga specificata (`insert_line`),
        che è un indice 1-based. Se `insert_line` è 0, il testo viene
        inserito all'inizio del file.
        
        Args:
            file_path (str): Il percorso del file da modificare.
            insert_line (int): Il numero di riga (1-based) dopo la quale
                               inserire il nuovo testo. Usare 0 per l'inizio.
            new_str (str): Il testo da inserire.
            
        Returns:
            str: Un messaggio di successo che indica l'avvenuto inserimento.
            
        Raises:
            FileNotFoundError: Se il file non esiste.
            IndexError: Se il numero di riga specificato è fuori dall'intervallo
                        valido del file.
            PermissionError: Se i permessi di scrittura sono negati.
        """
        try:
            abs_path = self._validate_path(file_path)

            if not os.path.exists(abs_path):
                raise FileNotFoundError("File not found")

            # Create backup before modifying
            self._backup_file(abs_path)

            with open(abs_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Handle line endings
            if lines and not lines[-1].endswith("\n"):
                new_str = "\n" + new_str

            # Insert at the beginning if insert_line is 0
            if insert_line == 0:
                lines.insert(0, new_str + "\n")
            # Insert after the specified line
            elif insert_line > 0 and insert_line <= len(lines):
                lines.insert(insert_line, new_str + "\n")
            else:
                raise IndexError(
                    f"Line number {insert_line} is out of range. File has {len(lines)} lines."
                )

            with open(abs_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            return f"Successfully inserted text after line {insert_line}"

        except ValueError as e:
            raise ValueError(str(e))
        except PermissionError:
            raise PermissionError("Permission denied. Cannot modify file.")
        except Exception as e:
            raise type(e)(str(e))

    def undo_edit(self, file_path: str) -> str:
        """
        Annulla l'ultima modifica a un file, ripristinando il backup più recente.

        Questo metodo cerca l'ultimo file di backup creato per il file specificato
        e lo copia al posto del file originale, annullando così l'ultima modifica.

        Args:
            file_path (str): Il percorso del file di cui annullare le modifiche.

        Returns:
            str: Un messaggio di successo che indica che il ripristino è avvenuto.

        Raises:
            FileNotFoundError: Se il file originale o un backup non esiste.
            PermissionError: Se i permessi di scrittura sono negati.
        """
        try:
            abs_path = self._validate_path(file_path)

            if not os.path.exists(abs_path):
                raise FileNotFoundError(f"Original file not found at {abs_path}")
            
            return self._restore_backup(abs_path)

        except ValueError as e:
            raise ValueError(str(e))
        except PermissionError:
            raise PermissionError("Permission denied. Cannot write to file.")
        except Exception as e:
            raise type(e)(str(e))
        try:
            abs_path = self._validate_path(file_path)

            if not os.path.exists(abs_path):
                raise FileNotFoundError("File not found")

            return self._restore_backup(abs_path)

        except ValueError as e:
            raise ValueError(str(e))
        except FileNotFoundError:
            raise FileNotFoundError("No previous edits to undo")
        except PermissionError:
            raise PermissionError("Permission denied. Cannot restore file.")
        except Exception as e:
            raise type(e)(str(e))