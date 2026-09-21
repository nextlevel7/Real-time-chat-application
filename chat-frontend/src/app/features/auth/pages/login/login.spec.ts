import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { provideRouter } from '@angular/router';
import { Login } from './login';

describe('Login', () => {
  let component: Login;
  let fixture: ComponentFixture<Login>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Login],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideNoopAnimations(),
        provideRouter([]),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Login);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have invalid login form initially', () => {
    expect(component.loginForm.valid).toBe(false);
  });

  it('should validate login form when valid credentials are provided', () => {
    component.loginForm.setValue({
      email: 'test@example.com',
      password: 'password123',
    });
    expect(component.loginForm.valid).toBe(true);
  });

  it('should require minimum 10 characters for registration password', () => {
    component.registerForm.setValue({
      username: 'validuser',
      email: 'user@example.com',
      password: 'short',
    });
    expect(component.registerForm.valid).toBe(false);
    expect(component.registerForm.get('password')?.hasError('minlength')).toBe(true);

    component.registerForm.patchValue({
      password: 'ValidPassword123!',
    });
    expect(component.registerForm.valid).toBe(true);
  });

  it('should switch selected tab', () => {
    component.onTabChange(1);
    expect(component.selectedTab()).toBe(1);
  });
});
