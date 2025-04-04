-- Tạo một View hiển thị thông tin chi tiết đơn hàng và người dùng
CREATE VIEW dbo.OrderDetailsView AS
SELECT 
    o.id AS order_id,
    o.sender_name,
    o.sender_phone,
    o.receiver_name,
    o.receiver_phone,
    o.receiver_address,
    o.shipping_method,
    o.payment_method,
    o.status AS order_status,
    o.created_at AS order_created_at,
    o.updated_at AS order_updated_at,
    u.name AS user_name,
    u.email AS user_email
FROM orders o
JOIN users u ON o.user_id = u.id;
