import io
from typing import Optional
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as patches 
import geobr 

from src.infrastructure.shared.map_styles import STYLES 

def plot_map(
    gdf: gpd.GeoDataFrame, 
    state_abbr: str, 
    column_to_plot: str, 
    title: str, 
    legend_label: str
) -> Optional[io.BytesIO]: 
   
    print(f"\n--- [Visualização] Iniciando desenho do mapa: '{title}' ---")
    
    style = STYLES.get('advanced_choropleth')
    if not style:
        print("❌ ERRO: O estilo 'advanced_choropleth' não foi encontrado no módulo STYLES.")
        return None

    try:
        # --- CARREGAMENTO E CONFIGURAÇÃO INICIAL ---
        print(" -> [Visualização] Buscando mapa do Brasil para usar como fundo...")
        brasil_gdf = geobr.read_state(code_state='all', year=2020) 
        
        fig, ax = plt.subplots(1, 1, figsize=(12, 12)) 
        ax.set_aspect('equal')
        ocean_patch = patches.Rectangle(
            (-180, -90), 360, 180,
            linewidth=0, edgecolor='none', facecolor='#a2d9f7', zorder=0
        )
        ax.add_patch(ocean_patch)

        print(" -> [Visualização] Desenhando camada de fundo (zorder=1)...")
        brasil_gdf.plot(
            ax=ax,
            color=style['context_layer']['facecolor'],
            edgecolor=style['context_layer']['edgecolor'],
            linewidth=style['context_layer']['linewidth'],
            zorder=1
        )
        
        print(f" -> [Visualização] Desenhando mapa coroplético de {state_abbr} (zorder=2)...")
        gdf[column_to_plot] = gdf[column_to_plot].fillna(0)
        vmax = gdf[column_to_plot].quantile(0.95)
        if vmax == 0: vmax = 10

        gdf.plot(
            ax=ax, 
            column=column_to_plot, 
            cmap=style['choropleth_layer']['cmap'],
            linewidth=style['choropleth_layer']['linewidth'],
            edgecolor=style['choropleth_layer']['edgecolor'],
            legend=True, 
            zorder=2,
            scheme='NaturalBreaks', 
            k=5,
            legend_kwds={
               'loc': 'lower center',          
                'bbox_to_anchor': (0.5, 0.0), 
                'ncol': 5,                    
                'frameon': False,             
                'labelcolor': STYLES.get('legend', {}).get('labelcolor', STYLES['advanced_choropleth']['title']['color']),
            }
        )

        print(" -> [Visualização] Ajustando estilo da legenda...")
        try:
            leg = ax.get_legend()
            if leg:
                
                for handle in leg.legend_handles: 
                    handle.set_marker('s')  
                    handle.set_markersize(17) 
                    handle.set_markeredgecolor('black') 
                    handle.set_markeredgewidth(0.5)
                
                
                for text in leg.get_texts():
                    original_label = text.get_text()
                    new_label = original_label.replace(", ", " - ")
                    text.set_text(new_label)

        except Exception as e:
            print(f" -> [Visualização] Aviso: Não foi possível modificar a legenda: {e}")

        # --- LÓGICA: AJUSTE DE ZOOM DINÂMICO (COM CORTE PARA PE) ---
        print(" -> [Visualização] Ajustando zoom e finalizando o mapa...")
        
        state_boundary = brasil_gdf[brasil_gdf['abbrev_state'] == state_abbr.upper()]
        
        if not state_boundary.empty:
            minx, miny, maxx, maxy = state_boundary.total_bounds
            
            if state_abbr.upper() == 'PE':
                print(" -> [Visualização] PE detectado. Cortando a longitude para focar no continente.")
                maxx = -34.5

            buffer_x = (maxx - minx) * 0.20 
            buffer_y = (maxy - miny) * 0.20
            ax.set_xlim(minx - buffer_x, maxx + buffer_x)
            ax.set_ylim(miny - buffer_y, maxy + buffer_y)

        ax.set_axis_off()
        
        # --- SALVAR EM MEMÓRIA ---
        print(f" -> [Visualização] Salvando mapa em buffer de memória...")
        buf = io.BytesIO()
        fig.savefig(
            buf, 
            format='png', 
            dpi=300, 
            bbox_inches='tight',
            pad_inches=0
        )
        buf.seek(0)
        
        plt.close(fig)
        print(f"--- [Visualização] ✅ Mapa gerado com sucesso! ---")
        return buf

    except Exception as e:
        print(f"❌ ERRO ao gerar a imagem do mapa: {e}")
        if 'fig' in locals() and fig is not None: 
            plt.close(fig)
        return None