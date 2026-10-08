import io
import geopandas as gpd
import geobr
import matplotlib.pyplot as plt
from typing import Optional
import matplotlib.patches as patches 


from src.infrastructure.shared.map_styles import STYLES, GENERAL_STYLE

class GetMapStateLayersUseCase:

    def execute(
        self,
        state_abbr: str,
        year: int,
        show_municipalities: bool,
        show_immediate: bool,
        show_intermediate: bool,
        use_zoom: bool, 

    ) -> Optional[io.BytesIO]:

        print(f"--- PASSO 1: CARREGANDO DADOS PARA {state_abbr.upper()} ({year}) ---")
        fig = None 

        try:
            estado_gdf = geobr.read_state(
                code_state=state_abbr, year=year, simplified=True
            )
        except Exception as e:
            print(f"❌ Falha: Erro ao carregar dados do estado: {e}")
            return None

        if estado_gdf.empty:
            print(f"❌ Falha: Estado '{state_abbr}' não encontrado.")
            return None

        code_state = int(estado_gdf["code_state"].iloc[0])
        nome_estado = estado_gdf["name_state"].iloc[0]
        
        print(" -> [Visualização] Buscando mapa do Brasil para usar como fundo e limites...")
        try:
            brasil_gdf = geobr.read_state(code_state='all', year=2020, simplified=True) 
        except Exception as e:
            print(f"❌ Falha: Erro ao carregar mapa do Brasil: {e}")
            return None

        
        plot_single_state_only = not (show_municipalities or show_immediate or show_intermediate)
        
        municipios_gdf = None
        if show_municipalities and not plot_single_state_only:
            print("Carregando dados de municípios...")
            municipios_br = geobr.read_municipality(year=year, simplified=True)
            municipios_gdf = municipios_br.query("code_state == @code_state")

        immediate_gdf = None
        if show_immediate and not plot_single_state_only:
            print("Carregando dados de regiões imediatas...")
            immediate_br = geobr.read_immediate_region(year=year, simplified=True)
            immediate_gdf = immediate_br.query("code_state == @code_state")

        intermediate_gdf = None
        if show_intermediate and not plot_single_state_only:
            print("Carregando dados de regiões intermediárias...")
            intermediate_br = geobr.read_intermediate_region(year=year, simplified=True)
            intermediate_gdf = intermediate_br.query("code_state == @code_state")


        
        print("\n--- PASSO 2: GERANDO MAPA ---")
        
        style = STYLES["state_regional_map"]
        
        fig, ax = plt.subplots(figsize=(10, 10), dpi=100)
        ax.set_aspect('equal')
        ax.set_facecolor('none')

        # 1. ADICIONAR FUNDO AZUL (OCEANO/CONTEXTO)
        print(" -> [Visualização] Adicionando patch de Oceano Azul...")
        ocean_patch = patches.Rectangle(
            (-180, -90), 360, 180, 
            linewidth=0, edgecolor='none', facecolor='#a2d9f7', zorder=0 
        )
        ax.add_patch(ocean_patch)

        # 2. PLOTAR O BRASIL INTEIRO COMO CAMADA de FUNDO
        print(" -> [Visualização] Desenhando mapa do Brasil inteiro (zorder=1)...")
        context_style = STYLES.get('advanced_choropleth', {}).get('context_layer', {
            'facecolor': "#000000", 
            'edgecolor': 'white', 
            'linewidth': 0.5
        })
        
        brasil_gdf.plot(
            ax=ax,
            color=context_style['facecolor'],
            edgecolor=context_style['edgecolor'],
            linewidth=context_style['linewidth'],
            zorder=1,
            legend=False 
        )
        
        # 3. PLOTAGEM CONDICIONAL DO ESTADO
        if plot_single_state_only:
            print(" -> [Visualização] MODO: Apenas Estado em Destaque (Azul).")
            estado_color = '#4682B4'
            estado_gdf.plot(
                ax=ax, 
                facecolor=estado_color, 
                edgecolor='black', 
                linewidth=1.5, 
                zorder=3, 
                legend=False 
                
            )
            
        else:
            print(" -> [Visualização] MODO: Camadas Regionais.")
            
            if show_municipalities and municipios_gdf is not None:
                municipios_gdf.plot(ax=ax, **style["municipality_coverage"], zorder=2, legend=False) 
            if show_immediate and immediate_gdf is not None:
                immediate_gdf.plot(ax=ax, facecolor="none", **style["immediate_region_line"], zorder=3, legend=False)
            if show_intermediate and intermediate_gdf is not None:
                intermediate_gdf.plot(ax=ax, facecolor="none", **style["intermediate_region_line"], zorder=4, legend=False)

            estado_gdf.plot(ax=ax, facecolor="none", **style["final_border"], zorder=5, legend=False)
            

       
        if use_zoom:
            
            print(" -> [Visualização] MODO ZOOM: Aplicando zoom dinâmico no estado...")
            
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
        else:
            
            print(" -> [Visualização] MODO NACIONAL: Aplicando zoom no Brasil.")
            minx_br, miny_br, maxx_br, maxy_br = brasil_gdf.total_bounds

            buffer_x_br = (maxx_br - minx_br) * 0.05
            buffer_y_br = (maxy_br - miny_br) * 0.05
            ax.set_xlim(minx_br - buffer_x_br, maxx_br + buffer_x_br)
            ax.set_ylim(miny_br - buffer_y_br, maxy_br + buffer_y_br)
            
        ax.set_axis_off()
        
        
        print("Salvando imagem em buffer...")
        try:
            buffer = io.BytesIO()
            fig.savefig(buffer, format="png", dpi=300, bbox_inches="tight", pad_inches=0)
            plt.close(fig) 
            buffer.seek(0) 
            print(f"--- ✅ Mapa gerado com sucesso! ---")
            return buffer
        except Exception as e:
            print(f"❌ Falha: Erro ao")