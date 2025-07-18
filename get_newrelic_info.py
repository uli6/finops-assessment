#!/usr/bin/env python3
"""
Script para obter informações do New Relic App
Execute: python get_newrelic_info.py
"""

import os
import requests
import json

def get_newrelic_app_info():
    """Obtém informações da aplicação no New Relic"""
    
    # Solicita a API Key
    api_key = input("Digite sua NEW_RELIC_API_KEY: ").strip()
    
    if not api_key:
        print("❌ API Key é obrigatória!")
        return
    
    headers = {
        'Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    # URL da API do New Relic
    url = "https://api.newrelic.com/graphql"
    
    # Query GraphQL para buscar aplicações
    query = """
    {
      actor {
        entitySearch(queryBuilder: {type: APPLICATION}) {
          results {
            entities {
              guid
              name
              domain
              type
              tags {
                key
                values
              }
            }
          }
        }
      }
    }
    """
    
    try:
        print("🔍 Buscando aplicações no New Relic...")
        response = requests.post(url, headers=headers, json={'query': query})
        response.raise_for_status()
        
        data = response.json()
        
        if 'errors' in data:
            print(f"❌ Erro na API: {data['errors']}")
            return
        
        entities = data['data']['actor']['entitySearch']['results']['entities']
        
        if not entities:
            print("❌ Nenhuma aplicação encontrada!")
            return
        
        print("\n📱 Aplicações encontradas:")
        print("=" * 80)
        
        for i, entity in enumerate(entities, 1):
            print(f"\n{i}. Nome: {entity['name']}")
            print(f"   GUID: {entity['guid']}")
            print(f"   Tipo: {entity['type']}")
            print(f"   Domínio: {entity['domain']}")
            
            # Extrai APP_ID do GUID (primeiros caracteres)
            app_id = entity['guid'].split('-')[0] if '-' in entity['guid'] else entity['guid'][:8]
            print(f"   APP_ID (estimado): {app_id}")
            
            if entity['tags']:
                print("   Tags:")
                for tag in entity['tags']:
                    print(f"     {tag['key']}: {', '.join(tag['values'])}")
        
        print("\n" + "=" * 80)
        print("💡 Para o finops-assessment, use o GUID e APP_ID da aplicação correspondente")
        print("💡 Se não encontrar, verifique se a aplicação está sendo monitorada pelo New Relic")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

def get_entity_guid_by_name(api_key, app_name="finops-assessment"):
    """Busca GUID específico por nome da aplicação"""
    
    headers = {
        'Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    url = "https://api.newrelic.com/graphql"
    
    query = f"""
    {{
      actor {{
        entitySearch(queryBuilder: {{name: "{app_name}", type: APPLICATION}}) {{
          results {{
            entities {{
              guid
              name
              domain
              type
            }}
          }}
        }}
      }}
    }}
    """
    
    try:
        response = requests.post(url, headers=headers, json={'query': query})
        response.raise_for_status()
        
        data = response.json()
        entities = data['data']['actor']['entitySearch']['results']['entities']
        
        if entities:
            entity = entities[0]
            print(f"\n🎯 Aplicação encontrada: {entity['name']}")
            print(f"   GUID: {entity['guid']}")
            print(f"   APP_ID: {entity['guid'].split('-')[0] if '-' in entity['guid'] else entity['guid'][:8]}")
            return entity['guid']
        else:
            print(f"❌ Aplicação '{app_name}' não encontrada!")
            return None
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

if __name__ == "__main__":
    print("🔧 New Relic App Info Finder")
    print("=" * 40)
    
    # Opção 1: Listar todas as aplicações
    print("\n1. Listar todas as aplicações")
    print("2. Buscar aplicação específica (finops-assessment)")
    
    choice = input("\nEscolha uma opção (1 ou 2): ").strip()
    
    if choice == "2":
        api_key = input("Digite sua NEW_RELIC_API_KEY: ").strip()
        if api_key:
            get_entity_guid_by_name(api_key)
    else:
        get_newrelic_app_info() 