// Runs the Medical claim flow on a Windows Jenkins agent automatically after
// every successful RSS deployment to stage, then publishes and emails the
// executive summary report.
//
// E-sign approval needs a person's biometric, so this unattended job stops
// once the e-sign request is sent (ESIGN_APPROVAL=false).

// Exact name of the Jenkins job that deploys RSS to stage (use
// 'folder/job-name' if it is inside a folder).
def DEPLOY_JOB_NAME = 'CHANGE_ME-rss-stage-deploy'
// Comma-separated email addresses that receive the report.
def REPORT_RECIPIENTS = 'CHANGE_ME@rajyasabha.digital'

pipeline {
    agent any

    triggers {
        // Start this job whenever the stage deployment job succeeds.
        upstream(upstreamProjects: DEPLOY_JOB_NAME, threshold: hudson.model.Result.SUCCESS)
    }

    options {
        disableConcurrentBuilds()
        timeout(time: 45, unit: 'MINUTES')
    }

    environment {
        APP_BASE_URL = 'https://test.rajyasabha.digital/login?login=email'
        BROWSER_HEADLESS = 'true'
        BROWSER_SLOW_MO = '0'
        ESIGN_APPROVAL = 'false'
        PYTHONIOENCODING = 'utf-8'
    }

    stages {
        stage('Setup') {
            steps {
                bat '''
                    if not exist venv\\Scripts\\python.exe python -m venv venv
                    venv\\Scripts\\python.exe -m pip install --upgrade pip
                    venv\\Scripts\\python.exe -m pip install -r requirements.txt
                    venv\\Scripts\\python.exe -m playwright install chromium
                '''
            }
        }

        stage('Wait for stage') {
            steps {
                // A fresh deployment can take a moment to come up; wait up to
                // 10 minutes for the login page before testing.
                powershell '''
                    $deadline = (Get-Date).AddMinutes(10)
                    while ($true) {
                        try {
                            $response = Invoke-WebRequest -Uri $env:APP_BASE_URL -UseBasicParsing -TimeoutSec 30
                            if ($response.StatusCode -eq 200) { Write-Host "Stage is up"; break }
                        } catch { Write-Host "Stage not ready yet: $($_.Exception.Message)" }
                        if ((Get-Date) -gt $deadline) { throw "Stage did not come up within 10 minutes" }
                        Start-Sleep -Seconds 20
                    }
                '''
            }
        }

        stage('Medical claim') {
            steps {
                bat 'run_medical_e2e.bat'
            }
        }
    }

    post {
        always {
            // Copy the newest executive summary to a fixed name for publishing.
            powershell '''
                New-Item -ItemType Directory -Force -Path reports\\latest | Out-Null
                $latest = Get-ChildItem reports\\execution_summary_*.html -ErrorAction SilentlyContinue |
                    Sort-Object LastWriteTime -Descending | Select-Object -First 1
                if ($latest) { Copy-Item $latest.FullName reports\\latest\\index.html -Force }
            '''
            archiveArtifacts artifacts: 'reports/*.html, screenshots/*.png', allowEmptyArchive: true
            publishHTML(target: [
                reportDir: 'reports/latest',
                reportFiles: 'index.html',
                reportName: 'Test Report',
                keepAll: true,
                alwaysLinkToLastBuild: true,
                allowMissing: true
            ])
            emailext(
                to: REPORT_RECIPIENTS,
                subject: "RSS stage tests ${currentBuild.currentResult}: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: """Automated tests after the RSS stage deployment finished: ${currentBuild.currentResult}

Test report: ${env.BUILD_URL}Test_20Report/
Build log:   ${env.BUILD_URL}console

The executive summary report is attached.""",
                attachmentsPattern: 'reports/latest/index.html'
            )
        }
    }
}
