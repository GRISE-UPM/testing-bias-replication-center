import { Routes } from '@angular/router';
import { authGuard, roleGuard } from './auth/auth.guard';
import { Join } from './participation/join';
import { Requests } from './participation/requests';
import { Experiment } from './experiment/experiment';
import { Landing } from './landing/landing';
import { DevLogin } from './login/dev-login';

export const routes: Routes = [
  { path: '', component: Landing },
  { path: 'login', component: DevLogin },
  { path: 'experiment', component: Experiment, canActivate: [authGuard] },
  { path: 'join', component: Join, canActivate: [authGuard] },
  { path: 'requests', component: Requests, canActivate: [roleGuard('organizer')] },
  { path: '**', redirectTo: '' },
];
