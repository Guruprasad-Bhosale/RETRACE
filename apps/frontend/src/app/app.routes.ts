import { Routes } from '@angular/router';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { ProjectsComponent } from './pages/projects/projects.component';
import { AnalysesComponent } from './pages/analyses/analyses.component';
import { InvestigationsComponent } from './pages/investigations/investigations.component';
import { InvestigationDetailComponent } from './pages/investigations/investigation-detail.component';

export const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'projects', component: ProjectsComponent },
  { path: 'analyses', component: AnalysesComponent },
  { path: 'investigations', component: InvestigationsComponent },
  { path: 'investigations/:id', component: InvestigationDetailComponent },
  { path: '**', redirectTo: 'dashboard' },
];
