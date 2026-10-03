import { Routes } from '@angular/router';
import { LandingPageComponent } from './pages/landing/landing.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { ProjectsComponent } from './pages/projects/projects.component';
import { AnalysesComponent } from './pages/analyses/analyses.component';
import { InvestigationsComponent } from './pages/investigations/investigations.component';
import { InvestigationDetailComponent } from './pages/investigations/investigation-detail.component';
import { ObservabilityComponent } from './pages/observability/observability.component';
import { OperationsComponent } from './pages/operations/operations.component';
import { SettingsComponent } from './pages/settings/settings.component';

export const routes: Routes = [
  { path: '', component: LandingPageComponent, pathMatch: 'full' },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'projects', component: ProjectsComponent },
  { path: 'analyses', component: AnalysesComponent },
  { path: 'investigations', component: InvestigationsComponent },
  { path: 'investigations/:id', component: InvestigationDetailComponent },
  { path: 'observability', component: ObservabilityComponent },
  { path: 'operations', component: OperationsComponent },
  { path: 'settings', component: SettingsComponent },
  { path: '**', redirectTo: '' },
];

