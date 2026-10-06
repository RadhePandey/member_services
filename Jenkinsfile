// Runs the Medical claim flow on a Windows Jenkins agent.
// E-sign approval needs a person's biometric, so this unattended job stops
// once the e-sign request is sent (ESIGN_APPROVAL=false).
pipeline {
    agent any

    environment {
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

        stage('Medical claim') {
            steps {
                bat 'run_medical_e2e.bat'
            }
        }
    }

    post {
        always {
            // Executive summary report and failure screenshots.
            archiveArtifacts artifacts: 'reports/*.html, screenshots/*.png', allowEmptyArchive: true
        }
    }
}
