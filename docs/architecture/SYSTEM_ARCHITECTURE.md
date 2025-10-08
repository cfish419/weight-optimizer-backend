# System Architecture - Boeing 737 Weight & Balance Optimizer

## High-Level Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│  React Frontend     │  Mobile Apps      │  Agent Interfaces     │
│  - Dashboard        │  - Ramp Agent     │  - Operations         │
│  - Visualization    │  - Gate Agent     │  - Load Master        │
│  - Reports          │  - Maintenance    │  - Crew Interface     │
└─────────────────────────────────────────────────────────────────┘
                                │
                        ┌───────▼───────┐
                        │   API Gateway │
                        │   (FastAPI)   │
                        └───────┬───────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Baggage Service │  │  Sync Service   │  │ Offline Service │ │
│  │ - Tracking      │  │ - Real-time     │  │ - Queue Mgmt    │ │
│  │ - Optimization  │  │ - Conflict Res  │  │ - Heartbeat     │ │
│  │ - Validation    │  │ - Broadcasting  │  │ - Snapshots     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                      CORE ENGINE LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │Weight/Balance   │  │  Load Optimizer │  │ FAA Validator   │ │
│  │Calculator       │  │ - CG Positioning│  │ - Compliance    │ │
│  │- CG Calculation │  │ - Compartment   │  │ - Regulations   │ │
│  │- Weight Limits  │  │   Distribution  │  │ - Audit Trail   │ │
│  │- MAC Percentage │  │ - Ballast Calc  │  │ - Reporting     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │Baggage Repository│  │ Sync Repository │  │Offline Repository│ │
│  │- Flight Manifest│  │ - Update Queue  │  │ - Change Queue  │ │
│  │- Special Items  │  │ - Conflict Log  │  │ - Agent Status  │ │
│  │- Compartments   │  │ - Agent Tracking│  │ - Snapshots     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │     DATABASE          │
                    │   SQLite → PostgreSQL │
                    └───────────────────────┘
```

## Component Interaction Flow

### 1. Standard Baggage Processing Flow
```
Agent Input → API Gateway → Baggage Service → Weight Calculator → 
FAA Validator → Repository → Real-time Sync → All Connected Agents
```

### 2. Offline Agent Flow
```
Offline Agent → Local Storage → Queue Changes → 
Reconnect → Offline Service → Conflict Resolution → Sync Service
```

### 3. Gate Check Crisis Flow
```
Gate Agent → Priority Queue → Immediate Recalculation → 
Load Optimizer → Ballast Recommendation → Broadcast Update
```

## Data Flow Architecture

### Real-time Synchronization
```
┌─────────────┐    WebSocket    ┌─────────────┐
│Operations   │◄──────────────►│Sync Engine  │
│Agent        │                │             │
└─────────────┘                └─────────────┘
                                       │
┌─────────────┐    WebSocket           │
│Ramp Agent   │◄───────────────────────┤
│(Offline     │                        │
│Capable)     │                        │
└─────────────┘                        │
                                       │
┌─────────────┐    WebSocket           │
│Load Master  │◄───────────────────────┘
│Interface    │
└─────────────┘
```

### Offline Data Management
```
┌─────────────┐    Local SQLite    ┌─────────────┐
│Offline Agent│◄─────────────────►│Local Storage│
└─────────────┘                   └─────────────┘
       │                                 │
       │ Reconnect                       │
       ▼                                 ▼
┌─────────────┐    Sync Queue     ┌─────────────┐
│Offline      │◄─────────────────►│Central      │
│Service      │                   │Repository   │
└─────────────┘                   └─────────────┘
```

## Security Architecture

### Authentication & Authorization
```
┌─────────────┐    JWT Token     ┌─────────────┐
│Agent Login  │─────────────────►│Auth Service │
└─────────────┘                  └─────────────┘
                                        │
                                        ▼
┌─────────────┐    Role-based    ┌─────────────┐
│API Gateway  │◄─────────────────│Authorization│
└─────────────┘                  └─────────────┘
```

### Data Validation Pipeline
```
Input Data → Schema Validation → Business Rules → 
FAA Compliance → Weight Limits → Dimensional Constraints
```

## Deployment Architecture

### Development Environment
```
┌─────────────┐    localhost:3000    ┌─────────────┐
│React Dev    │◄───────────────────►│FastAPI Dev  │
│Server       │                     │Server       │
└─────────────┘                     └─────────────┘
                                           │
                                           ▼
                                   ┌─────────────┐
                                   │SQLite DB    │
                                   └─────────────┘
```

### Docker Production Environment
```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Container                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │React Build  │  │FastAPI App  │  │SQLite/      │             │
│  │(Nginx)      │  │(Uvicorn)    │  │PostgreSQL   │             │
│  │Port: 80     │  │Port: 8000   │  │Port: 5432   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## Integration Points

### Phase 4: External Systems
```
┌─────────────┐    REST API     ┌─────────────┐
│Weight Scale │────────────────►│Integration  │
│Systems      │                 │Layer        │
└─────────────┘                 └─────────────┘
                                       │
┌─────────────┐    REST API            │
│Airline DCS  │◄───────────────────────┤
│Systems      │                        │
└─────────────┘                        │
                                       │
┌─────────────┐    WebSocket           │
│Mobile Apps  │◄───────────────────────┘
└─────────────┘
```

## Performance Considerations

### Calculation Engine Optimization
- **Sub-second Response**: Weight/balance calculations < 100ms
- **Concurrent Users**: Support 50+ simultaneous agents
- **Memory Management**: Efficient data structures for large flights
- **Caching Strategy**: Frequently accessed aircraft configurations

### Real-time Communication
- **WebSocket Connections**: Persistent connections for live updates
- **Message Queuing**: Reliable delivery for offline agents
- **Conflict Resolution**: Timestamp-based merge strategies
- **Heartbeat Monitoring**: 30-second agent connectivity checks

## Scalability Architecture

### Horizontal Scaling (Future)
```
┌─────────────┐    Load Balancer    ┌─────────────┐
│API Gateway  │◄──────────────────►│API Gateway  │
│Instance 1   │                    │Instance 2   │
└─────────────┘                    └─────────────┘
       │                                  │
       ▼                                  ▼
┌─────────────┐                   ┌─────────────┐
│Service      │    Shared DB      │Service      │
│Instance 1   │◄─────────────────►│Instance 2   │
└─────────────┘                   └─────────────┘
```

### Database Scaling
```
Phase 2: SQLite (Single file)
Phase 3: PostgreSQL (Single instance)
Phase 4: PostgreSQL (Read replicas)
Phase 5: Distributed database (Multi-region)
```

## Monitoring & Observability

### System Health Monitoring
- **API Response Times**: Track calculation performance
- **Agent Connectivity**: Monitor offline/online status
- **Error Rates**: Track validation failures and conflicts
- **Resource Usage**: Memory and CPU utilization

### Business Metrics
- **Flight Processing**: Successful optimizations per hour
- **Compliance Rate**: FAA validation success percentage
- **Agent Efficiency**: Time savings in loading operations
- **Fuel Optimization**: CG positioning accuracy metrics

## Disaster Recovery

### Data Backup Strategy
- **Real-time Replication**: Critical flight data
- **Point-in-time Recovery**: 24-hour retention
- **Offline Snapshots**: Agent data preservation
- **Configuration Backup**: Aircraft specifications

### Failover Mechanisms
- **Service Redundancy**: Multiple API instances
- **Database Failover**: Automatic replica promotion
- **Offline Mode**: Graceful degradation for agents
- **Manual Override**: Emergency operational procedures