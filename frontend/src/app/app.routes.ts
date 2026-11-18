import { Routes } from '@angular/router';
import { authGuard } from './auth/auth.guard';
import { Experiment } from './experiment/experiment';
import { Landing } from './landing/landing';
import { DevLogin } from './login/dev-login';

export const routes: Routes = [
  { path: '', component: Landing },
  { path: 'login', component: DevLogin },
  { path: 'experiment', component: Experiment, canActivate: [authGuard] },
  { path: '**', redirectTo: '' },
];
