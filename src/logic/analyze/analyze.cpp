#include <iostream>
#include <vector>
#include <string>
#include <cmath>
#include <map>
#include <set>
#include <algorithm>
#include <stdexcept>
#include <unordered_map>

#include "cnpy.h"
#include "sqlite3.h"
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <nlohman/json.hpp>

using json = nlohmann::json;

// ---------- Параметры полиномов Цернике ----------
const int NUM_COEFFS = 15;
static const int n_vals[15] = {0,1,1,2,2,2,3,3,3,3,4,4,4,4,4};
static const int m_vals[15] = {0,1,-1,0,-2,2,-1,1,-3,3,0,2,-2,4,-4};

inline double factorial(int n) {
    double res = 1.0;
    for (int i = 2; i <= n; ++i) res *= i;
    return res;
}

double radial_deriv(int n, int m_abs, double rho) {
    if ((n - m_abs) % 2 != 0) return 0.0;
    double sum = 0.0;
    for (int k = 0; k <= (n - m_abs) / 2; ++k) {
        if (n - 2*k == 0) continue;
        double term = pow(-1.0, k) * factorial(n - k) /
                      (factorial(k) * factorial((n + m_abs)/2 - k) *
                       factorial((n - m_abs)/2 - k));
        sum += term * (n - 2*k) * pow(rho, n - 2*k - 1);
    }
    return sum;
}

void zernike_and_deriv(int j, double x, double y,
                       double& Z, double& dZdx, double& dZdy) {
    if (j < 1 || j > NUM_COEFFS) { Z = dZdx = dZdy = 0.0; return; }
    int n = n_vals[j-1];
    int m = m_vals[j-1];
    double rho = sqrt(x*x + y*y);
    if (rho > 1.0) rho = 1.0;
    double theta = atan2(y, x);
    int m_abs = abs(m);

    double R = 0.0;
    for (int k = 0; k <= (n - m_abs)/2; ++k) {
        double term = pow(-1.0, k) * factorial(n - k) /
                      (factorial(k) * factorial((n + m_abs)/2 - k) *
                       factorial((n - m_abs)/2 - k));
        R += term * pow(rho, n - 2*k);
    }
    double dR = radial_deriv(n, m_abs, rho);

    double drho_dx = (rho < 1e-12) ? 0.0 : x / rho;
    double drho_dy = (rho < 1e-12) ? 0.0 : y / rho;
    double dtheta_dx = (rho < 1e-12) ? 0.0 : -y / (rho*rho);
    double dtheta_dy = (rho < 1e-12) ? 0.0 :  x / (rho*rho);

    if (m == 0) {
        Z = R;
        dZdx = dR * drho_dx;
        dZdy = dR * drho_dy;
    } else if (m > 0) {
        Z = R * cos(m * theta);
        dZdx = dR * drho_dx * cos(m * theta) + R * (-m * sin(m * theta)) * dtheta_dx;
        dZdy = dR * drho_dy * cos(m * theta) + R * (-m * sin(m * theta)) * dtheta_dy;
    } else {
        m = -m;
        Z = R * sin(m * theta);
        dZdx = dR * drho_dx * sin(m * theta) + R * (m * cos(m * theta)) * dtheta_dx;
        dZdy = dR * drho_dy * sin(m * theta) + R * (m * cos(m * theta)) * dtheta_dy;
    }
}

cv::Point2d computeCentroid(const cv::Mat& sub) {
    cv::Moments m = cv::moments(sub, false);
    if (m.m00 < 1e-6) return cv::Point2d(-1, -1);
    return cv::Point2d(m.m10 / m.m00, m.m01 / m.m00);
}

// Ключ для хэш-таблицы subapIdMap
struct FrameCell {
    int frame_id;
    int grid_col;
    int grid_row;
    bool operator==(const FrameCell& other) const {
        return frame_id == other.frame_id && grid_col == other.grid_col && grid_row == other.grid_row;
    }
};

struct FrameCellHash {
    std::size_t operator()(const FrameCell& k) const {
        return ((std::hash<int>()(k.frame_id) ^ (std::hash<int>()(k.grid_col) << 1)) >> 1) ^ (std::hash<int>()(k.grid_row) << 1);
    }
};

int main(int argc, char* argv[]) {
    try {
        std::string dbPath, methodName = "zernike_polynomials";
        int fileId = -1, startFrame = 0, endFrame = 999999;
        for (int i = 1; i < argc; ++i) {
            std::string arg = argv[i];
            if (arg == "--db" && i+1 < argc) dbPath = argv[++i];
            else if (arg == "--file-id" && i+1 < argc) fileId = std::stoi(argv[++i]);
            else if (arg == "--method" && i+1 < argc) methodName = argv[++i];
            else if (arg == "--start-frame" && i+1 < argc) startFrame = std::stoi(argv[++i]);
            else if (arg == "--end-frame" && i+1 < argc) endFrame = std::stoi(argv[++i]);
        }
        if (dbPath.empty() || fileId == -1) {
            std::cerr << "Usage: analyze.exe --db <path> --file-id <id> ..." << std::endl;
            return 1;
        }

        sqlite3* db;
        if (sqlite3_open(dbPath.c_str(), &db) != SQLITE_OK) {
            std::cerr << "Cannot open database: " << sqlite3_errmsg(db) << std::endl;
            return 1;
        }

        int methodId;
        {
            sqlite3_stmt* stmt;
            sqlite3_prepare_v2(db, "SELECT id FROM analysis_methods WHERE method_name=?", -1, &stmt, nullptr);
            sqlite3_bind_text(stmt, 1, methodName.c_str(), -1, SQLITE_STATIC);
            if (sqlite3_step(stmt) != SQLITE_ROW) {
                std::cerr << "Method not found\n";
                return 1;
            }
            methodId = sqlite3_column_int(stmt, 0);
            sqlite3_finalize(stmt);
        }

        // Собираем список кадров
        std::string q = "SELECT id, archive_path FROM frames WHERE file_id=" + std::to_string(fileId) +
                        " AND archive_path IS NOT NULL AND frame_index BETWEEN " +
                        std::to_string(startFrame) + " AND " + std::to_string(endFrame) +
                        " ORDER BY frame_index";
        sqlite3_stmt* stmt;
        sqlite3_prepare_v2(db, q.c_str(), -1, &stmt, nullptr);
        std::vector<std::pair<int, std::string>> frames;
        while (sqlite3_step(stmt) == SQLITE_ROW) {
            int fid = sqlite3_column_int(stmt, 0);
            const unsigned char* path = sqlite3_column_text(stmt, 1);
            if (path) frames.emplace_back(fid, reinterpret_cast<const char*>(path));
        }
        sqlite3_finalize(stmt);

        if (frames.empty()) {
            std::cerr << "No frames to process\n";
            return 1;
        }

        // --- Загружаем excluded ячейки ---
        std::map<int, std::set<std::pair<int,int>>> excludedMap;
        {
            std::string exclQuery = 
                "SELECT frame_id, grid_col, grid_row FROM subapertures "
                "WHERE frame_id IN (SELECT id FROM frames WHERE file_id = " + std::to_string(fileId) + ") "
                "AND excluded = 1";
            sqlite3_stmt* exclStmt;
            sqlite3_prepare_v2(db, exclQuery.c_str(), -1, &exclStmt, nullptr);
            while (sqlite3_step(exclStmt) == SQLITE_ROW) {
                int fid = sqlite3_column_int(exclStmt, 0);
                int col = sqlite3_column_int(exclStmt, 1);
                int row = sqlite3_column_int(exclStmt, 2);
                excludedMap[fid].insert({col, row});
            }
            sqlite3_finalize(exclStmt);
        }

        // --- Заранее загружаем все subaperture_id для всех кадров ---
        std::unordered_map<FrameCell, int, FrameCellHash> subapIdMap;
        {
            std::string subapQuery = 
                "SELECT frame_id, grid_col, grid_row, id FROM subapertures "
                "WHERE frame_id IN (SELECT id FROM frames WHERE file_id = " + std::to_string(fileId) + ")";
            sqlite3_stmt* sStmt;
            sqlite3_prepare_v2(db, subapQuery.c_str(), -1, &sStmt, nullptr);
            while (sqlite3_step(sStmt) == SQLITE_ROW) {
                int fid = sqlite3_column_int(sStmt, 0);
                int col = sqlite3_column_int(sStmt, 1);
                int row = sqlite3_column_int(sStmt, 2);
                int sid = sqlite3_column_int(sStmt, 3);
                subapIdMap[{fid, col, row}] = sid;
            }
            sqlite3_finalize(sStmt);
        }

        // --- Предварительное построение матрицы плана (по первому кадру) ---
        cnpy::npz_t firstNpz = cnpy::npz_load(frames[0].second);
        cnpy::NpyArray metaArr = firstNpz["metadata"];
        int32_t* metaData = metaArr.data<int32_t>();
        int N = metaArr.shape[0];

        std::vector<cv::Point2d> normPos;
        double cx = 0.0, cy = 0.0;
        int validCount = 0;
        for (int i = 0; i < N; ++i) {
            if (metaData[i*7 + 6]) continue;
            int32_t x = metaData[i*7 + 2];
            int32_t y = metaData[i*7 + 3];
            int32_t sw = metaData[i*7 + 4];
            int32_t sh = metaData[i*7 + 5];
            cx += x + sw/2.0;
            cy += y + sh/2.0;
            validCount++;
        }
        if (validCount == 0) { std::cerr << "No valid cells\n"; return 1; }
        cx /= validCount;
        cy /= validCount;

        double max_dist = 0.0;
        for (int i = 0; i < N; ++i) {
            if (metaData[i*7 + 6]) continue;
            double nx = metaData[i*7 + 2] + metaData[i*7 + 4]/2.0 - cx;
            double ny = metaData[i*7 + 3] + metaData[i*7 + 5]/2.0 - cy;
            double d = sqrt(nx*nx + ny*ny);
            if (d > max_dist) max_dist = d;
        }
        if (max_dist == 0.0) max_dist = 1.0;

        int M_rows = 0;
        for (int i = 0; i < N; ++i) {
            if (metaData[i*7 + 6]) continue;
            double nx = (metaData[i*7 + 2] + metaData[i*7 + 4]/2.0 - cx) / max_dist;
            double ny = (metaData[i*7 + 3] + metaData[i*7 + 5]/2.0 - cy) / max_dist;
            if (nx*nx + ny*ny > 1.0) continue;
            normPos.emplace_back(nx, ny);
            M_rows++;
        }

        if (M_rows == 0) { std::cerr << "No cells inside unit circle\n"; return 1; }

        cv::Mat M(2*M_rows, NUM_COEFFS, CV_64F);
        for (int i = 0; i < M_rows; ++i) {
            double x = normPos[i].x;
            double y = normPos[i].y;
            for (int j = 1; j <= NUM_COEFFS; ++j) {
                double Z, dZx, dZy;
                zernike_and_deriv(j, x, y, Z, dZx, dZy);
                M.at<double>(2*i, j-1) = dZx;
                M.at<double>(2*i+1, j-1) = dZy;
            }
        }

        cv::Mat M_pinv;
        cv::invert(M.t() * M, M_pinv, cv::DECOMP_SVD);
        M_pinv = M_pinv * M.t();

        // Основной цикл обработки кадров
        int total = static_cast<int>(frames.size());
        int processed = 0;

        // Транзакция
        sqlite3_exec(db, "BEGIN TRANSACTION", nullptr, nullptr, nullptr);

        const char* insMeasSql = 
            "INSERT OR REPLACE INTO subap_measurements "
            "(subaperture_id, method_id, measurement_data) VALUES (?, ?, ?)";

        for (const auto& [frame_id, npzPath] : frames) {
            cnpy::npz_t npz = cnpy::npz_load(npzPath);
            cnpy::NpyArray subArr = npz["subapertures"];
            cnpy::NpyArray frameMetaArr = npz["metadata"];
            if (subArr.shape[0] == 0) continue;

            int h = subArr.shape[1];
            int w = subArr.shape[2];
            uint8_t* subData = subArr.data<uint8_t>();
            int32_t* fmeta = frameMetaArr.data<int32_t>();

            const auto& exclSet = excludedMap[frame_id];

            cv::Mat b(2*M_rows, 1, CV_64F, cv::Scalar(0));
            int row = 0;
            bool hasData = false;

            for (int i = 0; i < frameMetaArr.shape[0] && row < M_rows; ++i) {
                int32_t col = fmeta[i*7 + 0];
                int32_t rowIdx = fmeta[i*7 + 1];
                if (exclSet.count({col, rowIdx})) continue;

                cv::Mat subImg(h, w, CV_8UC1, subData + i*h*w);
                cv::Point2d centroid = computeCentroid(subImg);
                if (centroid.x < 0) continue;

                double intensity = cv::sum(subImg)[0];

                // Быстрый поиск subaperture_id
                int subap_id = -1;
                auto it = subapIdMap.find({frame_id, col, rowIdx});
                if (it != subapIdMap.end()) {
                    subap_id = it->second;
                }

                if (subap_id > 0) {
                    json meas;
                    meas["centroid_x"] = centroid.x;
                    meas["centroid_y"] = centroid.y;
                    meas["intensity"] = intensity;
                    std::string jsonStr = meas.dump();

                    sqlite3_stmt* insStmt;
                    sqlite3_prepare_v2(db, insMeasSql, -1, &insStmt, nullptr);
                    sqlite3_bind_int(insStmt, 1, subap_id);
                    sqlite3_bind_int(insStmt, 2, methodId);
                    sqlite3_bind_text(insStmt, 3, jsonStr.c_str(), -1, SQLITE_TRANSIENT);
                    sqlite3_step(insStmt);
                    sqlite3_finalize(insStmt);
                }

                double dx = centroid.x - fmeta[i*7 + 4]/2.0;
                double dy = centroid.y - fmeta[i*7 + 5]/2.0;
                b.at<double>(2*row, 0) = dx;
                b.at<double>(2*row+1, 0) = dy;
                hasData = true;
                row++;
            }

            if (!hasData) continue;

            cv::Mat coeffs = M_pinv * b;
            cv::Mat residual = M * coeffs - b;
            double rms = cv::norm(residual) / sqrt(2.0 * M_rows);

            json result;
            result["coefficients"] = std::vector<double>(coeffs.begin<double>(), coeffs.end<double>());
            result["rms"] = rms;
            std::string jsonStr = result.dump();

            sqlite3_stmt* insResStmt;
            const char* sqlRes = "INSERT OR REPLACE INTO frame_analysis_results (frame_id, method_id, result_data) VALUES (?, ?, ?)";
            sqlite3_prepare_v2(db, sqlRes, -1, &insResStmt, nullptr);
            sqlite3_bind_int(insResStmt, 1, frame_id);
            sqlite3_bind_int(insResStmt, 2, methodId);
            sqlite3_bind_text(insResStmt, 3, jsonStr.c_str(), -1, SQLITE_TRANSIENT);
            sqlite3_step(insResStmt);
            sqlite3_finalize(insResStmt);

            processed++;
            std::cout << "PROGRESS " << processed << "/" << total << std::endl;
        }

        sqlite3_exec(db, "COMMIT", nullptr, nullptr, nullptr);
        sqlite3_close(db);
        std::cout << "ANALYSIS_COMPLETE" << std::endl;
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Fatal exception: " << e.what() << std::endl;
        return 1;
    }
}