[![bpa](https://github.com/RuiRomano/demos-cicd-salessense/actions/workflows/bpa.yml/badge.svg)](https://github.com/RuiRomano/demos-cicd-salessense/actions/workflows/bpa.yml) [![deploy](https://github.com/RuiRomano/demos-cicd-salessense/actions/workflows/deploy.yml/badge.svg)](https://github.com/RuiRomano/demos-cicd-salessense/actions/workflows/deploy.yml)


This repository demonstrates a Fabric CI/CD scenario using [fabric-cli](https://aka.ms/fabric-cli) and GitHub. It can be easily adapted to other use cases.  

- All source code is located in the [\src](/src/) folder.  
- Developers should work in isolation within a feature branch.  
- Pull requests to the main branch trigger a best practices analysis pipeline, [bpa.yml](./.github/workflows/bpa.yml), for both semantic models and reports. This process leverages community tools such as [Tabular Editor](https://github.com/TabularEditor/) and [PBI-Inspector](https://github.com/NatVanG/PBI-InspectorV2).  
- Upon a successful merge into the main branch, the deployment pipeline, [deploy.yml](./.github/workflows/deploy.yml), is triggered to ensure automated deployment to the `development` environment.  
- The deployment pipeline, [deploy.yml](./.github/workflows/deploy.yml), also runs daily on a scheduled trigger to deploy to the `production` environment.  

## Instructions

- Fork the repo.
- Configure required [Github secrets and variables](#secrets-and-variables) in your repo.
- Run the [deploy](/.github/workflows/deploy.yml) Github workflow to deploy into your tenant.

### Run scripts locally

Make sure you have the [Fabric CLI](https://github.com/microsoft/fabric-cli) installed. If not, run:
```bash
$ pip install ms-fabric-cli
```

### Secrets and variables

Before running the Github Action, ensure you configure the following [GitHub action secrets and variables](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions):

| Name            | Type   | Value                |
|-----------------|--------|----------------------|
| `FABRIC_CLIENT_ID`       | Secret | [Service Principal](https://learn.microsoft.com/en-us/entra/identity-platform/howto-create-service-principal-portal) client ID from your tenant   |
| `FABRIC_CLIENT_SECRET`   | Secret | Service Principal secret |
| `FABRIC_TENANT_ID` | Secret | Your tenant ID |
| `FABRIC_ADMIN_UPNS` | Variable | User [Entra object ID](https://learn.microsoft.com/en-us/partner-center/account-settings/find-ids-and-domain-names#find-the-user-object-id) that will be assigned to the items created by the service principal |
| `FABRIC_CAPACITY` | Variable | Your [Fabric Capacity](https://learn.microsoft.com/en-us/fabric/admin/capacity-settings?tabs=power-bi-premium) name, required to deploy Fabric items such as data pipelines |

## Topology

```mermaid
flowchart TB

    subgraph GitHub
        direction TB
        feature[feature branch]:::gh_branch
        main[main branch]:::gh_branch
        build[build pipeline - BPA rules]:::gh_action
        deploy[deploy pipeline]:::gh_action        
    end

    data_dev[(Files - Dev)]

    subgraph Dev
        direction TB
        
        subgraph workspace_dev[Fabric dev workspace]
            datapipeline_dev[data pipeline]
            notebook_dev[notebook]
            lakehouse_dev[lakehouse]
            semanticmodel_dev[semantic model]
            reports_dev[reports]
        end     

        data_dev-->datapipeline_dev
        datapipeline_dev-->lakehouse_dev
        notebook_dev-->lakehouse_dev
        semanticmodel_dev-->reports_dev
        lakehouse_dev-->semanticmodel_dev
    end

    data_prd[(Files - Prod)]

    subgraph Prod
        direction LR
        
        subgraph workspace_data[Fabric data workspace]
            datapipeline_prd[data pipeline]
            notebook_prd[notebook]
            lakehouse_prd[lakehouse] 
        end
        subgraph workspace_analytics[Fabric analytics workspace]
            semanticmodel_prd[semantic model]
            reports_prd[reports]
        end        
                
        data_prd-->datapipeline_prd
        
        datapipeline_prd-->lakehouse_prd
        notebook_prd-->lakehouse_prd
        semanticmodel_prd-->reports_prd    
        lakehouse_prd---semanticmodel_prd
    end
    
    feature-- PR --->build-- merge --> main --> deploy --> Dev
    
    deploy-- schedule every day --->Prod

    classDef gh_action fill: #1E90FF, color:white;
    classDef gh_branch fill:#e8b63e;    

```
