package com.arrears.manager.presentation.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.arrears.manager.presentation.auth.LoginScreen
import com.arrears.manager.presentation.auth.LoginViewModel
import com.arrears.manager.presentation.home.HomeScreen
import com.arrears.manager.presentation.loans.LoanProcessingScreen
import com.arrears.manager.presentation.loans.BranchComparisonScreen
import com.arrears.manager.presentation.loans.BranchComparisonViewModel
import com.arrears.manager.presentation.settings.SettingsScreen

sealed class Screen(val route: String) {
    object Login : Screen("login")
    object Home : Screen("home")
    object LoanProcessing : Screen("loan_processing/{type}") {
        fun createRoute(type: String) = "loan_processing/$type"
    }
    object BranchComparison : Screen("branch_comparison")
    object Settings : Screen("settings")
}

@Composable
fun ArrearsNavHost(
    navController: NavHostController = rememberNavController()
) {
    val loginViewModel: LoginViewModel = hiltViewModel()
    val isLoggedIn by loginViewModel.isLoggedIn.collectAsState(initial = false)
    
    NavHost(
        navController = navController,
        startDestination = Screen.Home.route // Always start at Home
        // startDestination = if (isLoggedIn) Screen.Home.route else Screen.Login.route
    ) {
        composable(Screen.Login.route) {
            LoginScreen(
                onLoginSuccess = {
                    navController.navigate(Screen.Home.route) {
                        popUpTo(Screen.Login.route) { inclusive = true }
                    }
                }
            )
        }
        
        composable(Screen.Home.route) {
            HomeScreen(
                onNavigateToLoanProcessing = { type ->
                    if (type == "branch_comparison") {
                        navController.navigate(Screen.BranchComparison.route)
                    } else {
                        navController.navigate(Screen.LoanProcessing.createRoute(type))
                    }
                },
                onNavigateToSettings = {
                    navController.navigate(Screen.Settings.route)
                },
                onLogout = {
                    navController.navigate(Screen.Login.route) {
                        popUpTo(0) { inclusive = true }
                    }
                }
            )
        }
        
        composable(Screen.LoanProcessing.route) { backStackEntry ->
            val type = backStackEntry.arguments?.getString("type") ?: ""
            LoanProcessingScreen(
                processingType = type,
                onNavigateBack = { navController.popBackStack() }
            )
        }
        
        composable(Screen.BranchComparison.route) {
            val branchViewModel: BranchComparisonViewModel = hiltViewModel()
            BranchComparisonScreen(
                viewModel = branchViewModel,
                onNavigateBack = { navController.popBackStack() },
                onDownload = { url ->
                    // Handle download - open URL
                }
            )
        }
        
        composable(Screen.Settings.route) {
            SettingsScreen(
                onNavigateBack = { navController.popBackStack() }
            )
        }
    }
}
