import pandas as pd
import numpy as np
import plotly.graph_objects as go
from collections import defaultdict
import os
import math
from typing import Dict, Tuple
import streamlit as st

class ChordDiagramAnalyzer:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = None 
        self.transitions = defaultdict(lambda: defaultdict(int))
        self.categories = set()
        self.visit_counts = defaultdict(int)
        
        # Definimos los grupos y colores como en el TreeMap
        self.groups = {
            'Bienvenue': ['bienvenue', 'mes-fermes', 'Mon Compte','account-confirm','auth','ma-ferme'],
            'Paramètrer': ['Dessiner mes parcelles', 'Paramétrer ma ferme', 'Mes intrants','Semences et plants', 'Mes tâches'],
            'Planifier': ['Mes itinéraires de culture', 'Mes planifications'],
            'Cultiver': ['Plan de Culture', 'Fiches de culture', 'Mes implantations', 'Mon semainier', 'Mon prévisionnel de récoltes', 'mes-observations'],
            'Diffuser': ['Mes semences et plants', 'Ma traçabilité', 'Gestion de stock', 'Consommations intrants', 'Analyse des ventes'],
            'Tutorial': ['tutorial']
        } 
        
        self.group_colors = {
            'Bienvenue': '#FF9E9E',
            'Paramètrer': '#FFD580',
            'Planifier': '#A2D5A2',
            'Cultiver': '#90CAF9',
            'Diffuser': '#C1A4D9',
            'Tutorial': '#FF0000'  # Color rojo intenso para Tutorial
        }
        
        # Crear un mapeo de categoría a grupo y color
        self.category_to_group = {}
        self.category_to_color = {}
        for group_name, categories in self.groups.items():
            for category in categories:
                self.category_to_group[category] = group_name
                self.category_to_color[category] = self.group_colors[group_name]
        
    def load_data(self):
        """Carga y prepara los datos básicos."""
        try:
            self.df = pd.read_csv(self.file_path)
            self.df['category'] = self.df['category'].astype(str)
            self.df = self.df.sort_values(['person.properties.email', 'datetime']).reset_index(drop=True)
            
            self.visit_counts = self.df['category'].value_counts().to_dict()
            
        except Exception as e:
            print(f"Error al cargar los datos: {str(e)}")
            return None
        
    def analyze_transitions(self):
        """Analiza las transiciones entre categorías."""
        try:
            categories = self.df['category'].tolist()
            emails = self.df['person.properties.email'].tolist()
            
            for i in range(len(categories) - 1):
                if emails[i] == emails[i + 1]:  # Solo contar transiciones del mismo usuario
                    source = categories[i]
                    target = categories[i + 1]
                    
                    if source != target:
                        self.transitions[source][target] += 1
                        self.categories.add(source)
                        self.categories.add(target)
                    
            print(f"Análisis completado. Categorías únicas: {len(self.categories)}")
            
        except Exception as e:
            print(f"Error en el análisis de transiciones: {str(e)}")
            raise

    def create_chord_diagram(self, min_value: int = 2): # min 2 es 
        """Crea un diagrama de cuerdas usando Plotly con colores por grupo."""
        try:
            categories = sorted(list(self.categories))
            n = len(categories)
            
            # Calcular posiciones de los nodos agrupados por grupo
            node_positions = {}
            current_angle = 0 
            
            # Agrupar categorías por grupo
            grouped_categories = defaultdict(list)
            for cat in categories:
                group = self.category_to_group.get(cat, "Otros")
                grouped_categories[group].append(cat)
            
            # Asignar posiciones manteniendo las categorías del mismo grupo juntas
            for group in self.groups.keys():
                if group in grouped_categories:
                    group_cats = grouped_categories[group]
                    angle_slice = 2 * math.pi * len(group_cats) / n
                    
                    for i, cat in enumerate(group_cats):
                        
                        angle = current_angle + (i * angle_slice / len(group_cats)) 
                        x = math.cos(angle)
                        y = math.sin(angle)
                        node_positions[cat] = (x, y)
                    
                    current_angle += angle_slice
            
            fig = go.Figure()
            
            # Agregar las conexiones (cuerdas)
            for source in self.transitions:
                for target, value in self.transitions[source].items():
                    if value >= min_value:
                        x0, y0 = node_positions[source]
                        x1, y1 = node_positions[target]
                        
                        # Color basado en el grupo de origen
                        source_color = self.category_to_color.get(source, '#808080') # 
                        
                        control_scale = 0.5
                        cx = (x0 + x1) * control_scale
                        cy = (y0 + y1) * control_scale
                        
                        t = np.linspace(0, 1, 100) # para suavizar la curva , quiere decir que
                        x = (1-t)**2 * x0 + 2*(1-t)*t * cx + t**2 * x1
                        y = (1-t)**2 * y0 + 2*(1-t)*t * cy + t**2 * y1
                        
                        opacity = min(0.8, value / 10) # Opacidad basada en el valor de la transición
                        width = 1 + value / 10 #
                        
                        fig.add_trace(go.Scatter( 
                            x=x, y=y, 
                            mode='lines' ,
                            line=dict(
                                width=width,
                                color=f'rgba{tuple(int(source_color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + (opacity,)}' 
                            ),
                            hoverinfo='text',
                            text=f'{source} ({self.category_to_group.get(source)}) → {target} ({self.category_to_group.get(target)}): {value}' if value > 1 else f'{source} → {target}: {value}', 
                            showlegend=False
                        ))
            
            # Agregar los nodos
            for group_name in self.groups.keys():
                group_cats = grouped_categories[group_name]
                
                node_x = []
                node_y = []
                node_text = []
                node_sizes = []
                
                for cat in group_cats:
                    pos = node_positions[cat]
                    visits = self.visit_counts.get(cat, 0)
                    node_x.append(pos[0])
                    node_y.append(pos[1])
                    node_text.append(f"{cat}")
                    node_sizes.append(20 + min(30, visits / 50)) #si cambio 20 a 
                
                fig.add_trace(go.Scatter(
                    x=node_x, y=node_y,
                    mode='markers+text',
                    marker=dict(
                        size=node_sizes,
                        color=self.group_colors[group_name],
                        line=dict(color='white', width=2)
                    ),
                    text=node_text,
                    textposition='middle center',
                    name=group_name,
                    hoverinfo='text',
                    showlegend=True
                ))
            
            fig.update_layout(
                title=f"Diagramme de Cordes - Transitions entre catégories par groupe<br>{os.path.basename(self.file_path)}",
                showlegend=True,
                legend=dict(
                    title="Groupes",
                    yanchor="top",
                    y=0.99,
                    xanchor="right",
                    x=0.99
                ),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor='white',
                width=1200,
                height=1000
            )
            
            return fig
            
        except Exception as e:
            print(f"Error al crear el diagrama de cuerdas: {str(e)}")
            raise

def main():
    # Ruta al archivo CSV
    file_path = "DiagrammeCHORDS/Testeur_[18_09_et_24_10].csv"
    
    # Crear instancia del analizador
    analyzer = ChordDiagramAnalyzer(file_path)
    
    # Cargar y analizar datos
    analyzer.load_data()
    analyzer.analyze_transitions()
    
    # Crear y mostrar el diagrama
    fig = analyzer.create_chord_diagram(min_value=2)
    fig.show()

    # Guardar el diagrama como archivo HTML
    #fig.write_html("ChordDiagram_CLIENTS[20_09_et_25_11].html")


if __name__ == "__main__":
    main()
